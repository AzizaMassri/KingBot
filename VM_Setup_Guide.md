# KingBot VM Setup Guide

Follow these exact steps when you log into your fresh Linux Virtual Machine (assuming a standard Ubuntu/Debian server). These commands will get Docker installed and launch your complete KingBot stack natively on the VM.

## Step 0: Log into your VM
Before running any commands, you must connect to your VM from your Windows PC using SSH. Open Windows PowerShell or Command Prompt and type the following:

```bash
ssh rbot@100.75.143.100
```
> [!NOTE] 
> It will ask for your password (`rocket`). The characters will not show up on the screen as you type. This is a normal Linux security feature! Just type it out and hit Enter.

## Step 1: Install Docker & Docker Compose
Run the following commands individually to update your VM's package lists and install the Docker engine.

```bash
# Update the system packages
sudo apt update && sudo apt upgrade -y

# Install prerequisite packages
sudo apt install -y ca-certificates curl gnupg lsb-release

# Download and install Docker automatically
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose natively
sudo apt install docker-compose-plugin -y
```

## Step 2: Allow Running Docker Without 'sudo'
By default, you have to type `sudo docker`. This step gives your user direct permission.

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Activate the permission change immediately
newgrp docker
```

## Step 3a: Transfer Files Directly (Option A)
If you haven't uploaded your project to GitHub, the easiest way is to push it straight from your Windows terminal. Open a **new** Windows terminal (do not run this inside the VM login wrapper) and paste:
```bash
scp -r "C:\Users\aziza\OneDrive\Desktop\KingBot" rbot@100.75.143.100:~/KingBot
```

## Step 3b: Transfer Files via GitHub (Option B)
If your `KingBot` project is connected to a GitHub repository, you can pull it down to the VM directly!

**First**, on your Windows PC, make sure all your recent changes are pushed online:
```bash
git add .
git commit -m "UI Overhauls and rebranding"
git push
```

**Second**, inside your VM SSH terminal, run this exact command using your PAT:
```bash
git clone https://ROCKETexecdevs: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@github.com/ROCKETexecdevs/KingBot.git
```

> [!NOTE]
> **Getting an error?** If your terminal says `fatal: destination path 'KingBot' already exists`, this means the code is already on your VM! You do not need to clone it again. Instead, jump down to **Step 5** and use `git pull` to simply pull the new updates. 
> To completely wipe the VM's code and start fresh with a new clone, run `rm -rf ~/KingBot` first, then try the `git clone` command again.

> [!WARNING]
> Because GitHub ignores sensitive files like `.env`, you **must** manually recreate it on the VM before KingBot will launch!
> Navigate into the cloned folder (`cd KingBot`), type `nano .env`, and paste your Discord Token and Gemini API Keys exactly as they appear on your local machine. Press `Ctrl+X`, then `Y`, then `Enter` to save it!

## Step 3.5: Clear Out Conflicting Ports (Optional but recommended!)
If you ever installed PostgreSQL or RabbitMQ natively on this VM in the past, those old background services are still clinging to ports `5672` and `15672` (RabbitMQ), as well as `5432` (Postgres). Docker will throw an `"address already in use"` error if we don't clear them out.

Run these commands to permanently stop and disable those old native services so Docker can claim the ports:
```bash
# Stop and disable native RabbitMQ
sudo systemctl stop rabbitmq-server
sudo systemctl disable rabbitmq-server

# Stop and disable native PostgreSQL
sudo systemctl stop postgresql
sudo systemctl disable postgresql

# Force-kill anything else stubbornly holding onto the exact network ports:
sudo fuser -k 5672/tcp
sudo fuser -k 15672/tcp
sudo fuser -k 5432/tcp
```

## Step 4: Launch KingBot
Once the `KingBot` folder is successfully placed on the VM, dive into the directory and turn on the engine. 

```bash
# Navigate into the project folder
cd ~/KingBot

# Build the containers and start everything in the background!
docker compose up -d --build
```

> [!TIP]
> **Auto-Restart is Enabled:** We specifically coded `restart: unless-stopped` in your `docker-compose.yml` file. This means if you ever restart the VM server, the Docker Engine will automatically spin up KingBot, the Postgres database, and RabbitMQ the instant the machine turns back on! You will never need to manually start it.

## Useful Administrative Commands
If you ever need to manage the bot from the VM terminal:

*   **View live KingBot server logs:** 
    `docker logs -f kingbot_app`
*   **Stop the bot cleanly for an update:** 
    `docker compose down`
*   **Wipe everything (including the database) to start fresh:** 
    `docker compose down -v`

---

## Step 5: How to Update KingBot in the Future
Whenever you make future code edits on your Windows PC and need to get those changes live on the VM, follow this sequence:

### 1. Push from Windows PC to GitHub
Open a terminal in your local `KingBot` folder on Windows and push the changes:
```bash
git add .
git commit -m "Updating KingBot features"
git push
```

### 2. Pull down to the VM and Restart
SSH into your VM and pull the new updates down from GitHub. Depending on how you have KingBot running natively, follow the correct restart command:

```bash
cd ~/KingBot
git pull origin main
```

**If you added any new dependencies, make sure to install them (for non-Docker setups):**
```bash
pip install -r requirements.txt
```

**To Restart (If using Docker):**
Tell Docker to restart or instantly rebuild with the new code:
```bash
docker-compose restart
# Or, if you want to rebuild the full image:
docker compose up -d --build
```
> [!TIP]
> You do **not** need to run `docker compose down` first. Running `docker compose up -d --build` will automatically detect the new code, elegantly stop the old bot container, and instantly hot-swap the new container in its place without dropping your database!

**To Restart (If using Systemd service `kingbot.service`):**
```bash
sudo systemctl restart kingbot
```

**To Restart (If running manually):**
Stop the script using `Ctrl+C` and restart it:
```bash
python3 bot.py
```
