#!/usr/bin/env node
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
require('dotenv').config();
const {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { z } = require('zod');
const https = require('https');

// Define the server
const server = new Server(
    {
        name: 'psi-mcp',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// Define the tool
const CHECK_PERFORMANCE_TOOL = 'check_performance';

// API Key from environment variable
const API_KEY = process.env.PSI_API_KEY;

// Helper function to perform PageSpeed Insights request
const performRequest = (url, strategy) => {
    return new Promise((resolve, reject) => {
        let apiUrl = `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${encodeURIComponent(
            url
        )}&strategy=${strategy}`;
        if (API_KEY) {
            apiUrl += `&key=${API_KEY}`;
        }

        // Use console.error for logging so it doesn't interfere with MCP stdio transport
        console.error(`Analyzing ${strategy} performance for: ${url}...`);

        https
            .get(apiUrl, (res) => {
                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        try {
                            resolve(JSON.parse(data));
                        } catch (e) {
                            reject(new Error('Failed to parse JSON response'));
                        }
                    } else {
                        try {
                            const errorData = JSON.parse(data);
                            reject(
                                new Error(
                                    errorData.error.message || `API Error: ${res.statusCode}`
                                )
                            );
                        } catch (e) {
                            reject(new Error(`API Error: ${res.statusCode}`));
                        }
                    }
                });
            })
            .on('error', (err) => {
                reject(err);
            });
    });
};

// Helper to format the result
const formatResult = (strategy, data) => {
    const lighthouse = data.lighthouseResult;
    // Handle cases where lighthouseResult might be missing or structured differently on error,
    // though successful response usually has it.
    if (!lighthouse) {
        return `No lighthouse result found for ${strategy}`;
    }

    const score = lighthouse.categories.performance.score * 100;
    const metrics = lighthouse.audits;

    let output = `======== ${strategy.toUpperCase()} REPORT ========\n`;
    output += `Performance Score: ${score.toFixed(0)}\n`;
    output += '--------------------------------\n';
    output += `LCP (Largest Contentful Paint): ${metrics['largest-contentful-paint'].displayValue}\n`;
    output += `FCP (First Contentful Paint):   ${metrics['first-contentful-paint'].displayValue}\n`;
    output += `TBT (Total Blocking Time):      ${metrics['total-blocking-time'].displayValue}\n`;
    output += `CLS (Cumulative Layout Shift):  ${metrics['cumulative-layout-shift'].displayValue}\n`;
    output += `Speed Index:                    ${metrics['speed-index'].displayValue}\n`;
    output += '================================\n';

    return output;
};

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: CHECK_PERFORMANCE_TOOL,
                description:
                    'Analyze the mobile or desktop performance of a URL using Google PageSpeed Insights.',
                inputSchema: zodToJsonSchema(
                    z.object({
                        url: z.string().describe('The URL to analyze'),
                        strategy: z
                            .enum(['mobile', 'desktop'])
                            .optional()
                            .describe('The analysis strategy (mobile or desktop). Defaults to mobile.'),
                    })
                ),
            },
        ],
    };
});

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === CHECK_PERFORMANCE_TOOL) {
        const { url, strategy = 'mobile' } = request.params.arguments;

        try {
            const data = await performRequest(url, strategy);
            const formattedOutput = formatResult(strategy, data);

            return {
                content: [
                    {
                        type: 'text',
                        text: formattedOutput,
                    },
                ],
            };
        } catch (error) {
            console.error(`Error running PageSpeed Insights: ${error.message}`);
            let errorMessage = `Error running PageSpeed Insights: ${error.message}`;
            if (error.message.includes('Quota exceeded')) {
                errorMessage +=
                    '\n[Hint] API Key Missing or Quota Exceeded. To fix this, set PSI_API_KEY environment variable.';
            }

            return {
                content: [
                    {
                        type: 'text',
                        text: errorMessage,
                    },
                ],
                isError: true,
            };
        }
    }
    throw new Error('Tool not found');
});

// Helper to convert Zod schema to JSON schema (simplified)
// Ideally we should use zod-to-json-schema package, but simple schema we can construct manually or minimal converter
function zodToJsonSchema(schema) {
    // In a real robust implementation, use zod-to-json-schema. 
    // For this simple case with just url (string) and strategy (enum), we can hardcode or use a lighter approach if we didn't install the converter.
    // However, MCP SDK expects JSON Schema Draft 7.
    // Let's implement a minimal conversion for the object/string/enum we used.

    // Note: To be safe and compliant, usually better to install zod-to-json-schema.
    // But since I didn't add it to "npm install" list in previous step (my bad), I'll do a quick manual schema construction here 
    // that matches what "zod" describes.

    return {
        type: "object",
        properties: {
            url: {
                type: "string",
                description: "The URL to analyze"
            },
            strategy: {
                type: "string",
                enum: ["mobile", "desktop"],
                description: "The analysis strategy (mobile or desktop). Defaults to mobile."
            }
        },
        required: ["url"]
    };
}

// Start the server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('PageSpeed Insights MCP Server running on stdio');
}

main().catch((error) => {
    console.error('Server error:', error);
    process.exit(1);
});
