# YouTube Cookie Authentication Setup

YouTube now requires authentication for many videos due to bot protection. This guide explains how to configure cookies for the YouTube Transcript Extractor.

## Quick Setup

1. Copy `.env.example` to `.env`
2. Choose one of the authentication methods below
3. Update your `.env` file accordingly

## Method 1: Browser Cookie Extraction (Recommended)

This automatically extracts cookies from your browser where you're logged into YouTube.

### Setup:
```bash
# In your .env file, uncomment and set:
COOKIES_FROM_BROWSER=chrome
```

### Supported browsers:
- `chrome` - Google Chrome
- `firefox` - Mozilla Firefox
- `safari` - Safari (macOS only)
- `edge` - Microsoft Edge
- `chromium` - Chromium
- `brave` - Brave Browser
- `opera` - Opera
- `vivaldi` - Vivaldi

### Requirements:
- You must be logged into YouTube in the specified browser
- The browser should be closed when running the extractor (some browsers lock their cookie database)

## Method 2: Manual Cookie File

If browser extraction doesn't work, you can manually export cookies.

### Setup:
```bash
# In your .env file, uncomment and set the path:
COOKIES_FILE=/path/to/your/cookies.txt
```

### How to export cookies:

#### Using Browser Extensions:
1. **Chrome/Edge**: Install "Get cookies.txt LOCALLY" extension
2. **Firefox**: Install "cookies.txt" extension
3. Navigate to YouTube while logged in
4. Use the extension to export cookies in Netscape format
5. Save the file and update the `COOKIES_FILE` path in `.env`

#### Manual Export (Advanced):
For advanced users, you can use tools like `browser_cookie3` or extract cookies manually from browser developer tools.

## Testing

After setup, try running the extractor with a YouTube URL that previously failed. The error should be resolved.

## Troubleshooting

- **Public videos reported as "Private video"**: This is almost always caused by an
  outdated yt-dlp or YouTube bot-gating the default client. First run
  `pip install -U yt-dlp`. The extractor already prefers non-gated player clients;
  you can tune them with `YOUTUBE_PLAYER_CLIENTS` in `.env` (e.g.
  `tv,web_safari,mweb,android_vr`) or set it to `default` to use yt-dlp's defaults.
- **"Sign in to confirm you're not a bot"**: Your cookies are invalid or expired
- **Browser locked database**: Close your browser completely before running
- **Permission errors**: Check that the cookies file path is readable
- **Still not working**: Try Method 2 if Method 1 fails, or vice versa

## Security Note

Cookie files contain your login session. Keep them secure and don't share them.