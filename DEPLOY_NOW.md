# 🚀 Deploy Mosaic to Vercel (2 minutes)

## Step 1: Deploy from Terminal

```bash
cd /Users/jason/storycorps-mosaic
vercel
```

When prompted:
- **Set up and deploy?** → `Y`
- **Which scope?** → Select your account
- **Link to existing project?** → `N` (create new)
- **Project name?** → `mosaic` (or keep default)
- **Directory?** → `./` (current directory)
- **Override settings?** → `N`

## Step 2: Add Your API Key

After deployment completes:

1. Go to: https://vercel.com/dashboard
2. Click on your new `mosaic` project
3. Go to **Settings** tab
4. Click **Environment Variables**
5. Add new variable:
   - **Key**: `ANTHROPIC_API_KEY`
   - **Value**: Your Anthropic API key (get one at https://console.anthropic.com/)
   - **Environment**: Select all (Production, Preview, Development)
6. Click **Save**

## Step 3: Redeploy to Apply API Key

```bash
vercel --prod
```

## Step 4: Test Your Live App!

Visit your URL (shown after deployment) and try:
- "Tell me about families finding strength"
- "How do immigrants find belonging?"
- "Show me connections between rural and urban stories"

## Troubleshooting

If the chat doesn't work:
1. Check Vercel dashboard → Functions tab → Logs
2. Make sure API key is set correctly
3. Try redeploying: `vercel --prod --force`

## Your URLs

- **Production**: https://mosaic.vercel.app (or your custom domain)
- **Dashboard**: https://vercel.com/your-username/mosaic
- **Logs**: https://vercel.com/your-username/mosaic/functions