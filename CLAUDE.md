# SeedVr2Test Project Instructions

## Project Details
- **GitHub Repository**: https://github.com/Dreamrealai/SeedVr2Test
- **Deployed Site**: https://seedvr2test.netlify.app/
- **Source Repository**: https://github.com/IceClear/SeedVR2 (original SeedVR2 implementation)

## Infrastructure
- **RunPod Instance**: SeedVr2Test (using H100 PCIe GPU)
- **RunPod API Key**: Configured in RunPod CLI

## Available CLIs
- **Netlify CLI**: Installed and available for deployment management
- **Google Cloud CLI**: Installed for GCS and cloud operations
- **RunPod CLI**: Installed and configured for GPU instance management

## Important Instructions
1. **Always use the helper script** to push changes to GitHub after each fix
2. **Before using any CLI**, firecrawl the documentation to ensure using latest syntax and features
3. **Auto-push policy**: Automatically commit and push after fixing bugs or implementing features

## Helper Scripts
- Git push helper: Use the configured helper script for pushing to GitHub
- Located at: /Users/davidchen/Documents/mcp-automation/helpers/

## Development Workflow
1. Make changes to the codebase
2. Test locally when possible
3. Use helper script to commit and push to GitHub
4. Deploy updates via Netlify CLI if frontend changes
5. Update RunPod instance if backend/model changes