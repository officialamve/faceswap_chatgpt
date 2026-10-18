# Security and privacy

- The bot authorizes a single numeric Telegram user ID before media download.
- Never commit `.env`, bot tokens, model weights, or personal photographs.
- Use only images you are authorized to process and have appropriate consent to use.
- Non-consensual intimate imagery, sexualized deepfakes, impersonation fraud, and identity-based abuse are outside the intended use.
- Input and result files are placed in a private temporary workspace and removed after a job. Telegram may retain copies already sent or received.
- The webhook uses Telegram's `X-Telegram-Bot-Api-Secret-Token` header. Use a long random secret and keep it private.
- Report vulnerabilities privately to the repository maintainer; do not post credentials or images in issues.
