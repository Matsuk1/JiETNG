# Account Binding

Learn how to bind your SEGA ID to JiETNG to access your 『maimai でらっくす』 scores and records.

## Binding Mechanism

JiETNG uses a **web-based binding** approach with secure time-limited tokens. Your credentials are submitted through a secure web form rather than being entered in the chat.

:::warning Important
There is no command-line binding method. You cannot enter your credentials directly in the chat. All binding is done through a secure web interface.
:::

## Binding Your Account

### Step 1: Start the Binding Process

Send the command to the bot:

```
bind
```

### Step 2: Open the Binding URL

The bot will send a button with a unique URL, click it.

:::tip Token Expiration
Binding tokens expire after **2 minutes**. If it expires, simply send the `bind` command again to get a new token.
:::

### Step 3: Enter Your Credentials

The web form will ask you for:

- **Language**: Select your preferred language
- **SEGA ID**: Your SEGA account username
- **Password**: Your SEGA account password
- **Version**: Choose `jp` (Japan) or `intl` (International)

:::danger Security Tips
- Never share your SEGA credentials with anyone
- The bot does not store your password in plain text
- Only use the official binding URL provided by the bot
:::

### Step 4: Confirmation

After successful binding, the page will immediately show a success screen. Your score data will sync in the background, and the bot will notify you via LINE message once complete.

:::tip Background Update
The first-time score sync (`maimai update`) runs in the background and completes in seconds. You don't need to wait — feel free to close the page.
:::

## Checking Binding Status

Verify if your account is bound:

```
profile
getme
```

This will show your current binding information, including:
- SEGA ID
- Version (jp/intl)
- Language settings
- Personal information status

## Updating Account Settings (rebind)

Update your password, timezone, language or Aime settings without unbinding:

```
settings
rebind
```

The bot sends a web link with a form pre-filled with your current information (SEGA ID cannot be changed). You'll receive a confirmation immediately after submitting.

## Unbinding

Remove your SEGA ID from the bot:

```
unbind
```

:::warning Data Deletion
Unbinding will **permanently delete** all your stored data, including:
- SEGA credentials
- Score records
- Friend lists
- Personal information
- Language preferences

This action cannot be undone.
:::

## Version Selection

### Japan (jp)

If you play at arcades in Japan:
- Official Japanese 『maimai でらっくす』
- Standard and DX charts
- All Japan-exclusive songs
- URL: https://maimaidx.jp/maimai-mobile/

### International (intl)

If you play outside Japan:
- 『maimai でらっくす』 machines in other countries
- Song updates may lag behind JP version
- Different regional events
- URL: https://maimaidx-eng.com/maimai-mobile/

:::tip Choose the Right Version
Select the version that matches where you actually play 『maimai でらっくす』. You can change the version later via the `settings` command without unbinding.
:::

## Score Updates

After binding, you can manually update scores:

```
maimai update
```

This will fetch your latest scores from maimai NET and update the records in the bot.

:::tip Update Frequency
Score updates are queued and processed sequentially to avoid overloading SEGA servers. During peak times, your update may take a few minutes to complete.
:::

