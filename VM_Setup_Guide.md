# KingBot VM Setup Guide

Follow these exact steps when you log into your fresh Linux Virtual Machine (assuming a standard Ubuntu/Debian server). These commands will get Docker installed and launch your complete KingBot stack natively on the VM.

## Phase 1: VM Preparation & Installation

### Step 1: Log into your VM
Before running any commands, connect to your VM from your Windows PC using SSH. Open Windows PowerShell or Command Prompt and run:
```bash
ssh rbot@100.75.143.100
```
> [!NOTE] 
> It will ask for your password (`rocket`). The characters will not show up on the screen as you type. This is a normal Linux security feature! Just type it out and hit Enter.

### Step 2: Install Docker & Docker Compose V2
Run the following commands individually to update your VM's package lists and install the Docker engine along with the modern Docker Compose V2 plugin.

```bash
# Update the system packages
sudo apt update && sudo apt upgrade -y

# Install prerequisite packages
sudo apt install -y ca-certificates curl gnupg lsb-release

# Download and install Docker automatically
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose V2 natively
sudo apt install docker-compose-plugin -y
```

### Step 3: Allow Running Docker Without 'sudo'
By default, you have to type `sudo docker`. This step gives your user direct permission.

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Activate the permission change immediately
newgrp docker
```

---

## Phase 2: Transferring the Project

You have two options to get your code onto the VM. Choose the one that works best for you.

### Option A: Transfer Files Directly via SCP
If you haven't uploaded your project to GitHub, you can push it straight from your Windows terminal. Open a **new** Windows terminal (do not run this inside the VM) and paste:
```bash
scp -r "C:\Users\aziza\OneDrive\Desktop\KingBot" rbot@100.75.143.100:~/KingBot
```

### Option B: Clone via GitHub
If your `KingBot` project is on GitHub, you can pull it down to the VM directly.

**First**, on your Windows PC, make sure your changes are pushed:
```bash
git add .
git commit -m "UI Overhauls and rebranding"
git push
```

**Second**, inside your VM SSH terminal, run this exact command using your Personal Access Token (PAT):
```bash
git clone https://ROCKETexecdevs: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@github.com/ROCKETexecdevs/KingBot.git
```

> [!NOTE]
> **Getting an error?** If your terminal says `fatal: destination path 'KingBot' already exists`, the code is already on your VM! You do not need to clone it again. Instead, use `git pull` from inside the directory to get new updates. To completely wipe the VM's code and start fresh, run `rm -rf ~/KingBot` first, then try the clone command again.

---

## Phase 3: Preparing the Environment

### Step 4: Configure the `.env` File
> [!WARNING]
> Because GitHub ignores sensitive files like `.env`, you **must** manually recreate it on the VM before KingBot will launch!

1. Navigate into the cloned folder: `cd ~/KingBot`
2. Open the file editor: `nano .env`
3. Paste your Discord Token and Gemini API Keys exactly as they appear on your local machine.
4. Press `Ctrl+X`, then `Y`, then `Enter` to save it.

### Step 5: Clear Out Conflicting Ports (Optional but Recommended)
If you previously installed PostgreSQL or RabbitMQ natively on this VM, old background services might still be clinging to ports `5672`, `15672`, and `5432`. Docker will throw an `"address already in use"` error if we don't clear them out.

Run these commands to permanently stop and disable native services so Docker can claim the ports:
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

---

## Phase 4: Launching KingBot

Once the `KingBot` folder is set up and ports are cleared, start the engine!

```bash
# Navigate into the project folder
cd ~/KingBot

# Build the containers and start everything in the background!
docker compose up -d --build
```
*(Notice we use `docker compose` with a space, which is the syntax for Docker Compose V2).*

> [!TIP]
> **Auto-Restart is Enabled:** Your `docker-compose.yml` file uses `restart: unless-stopped`. This means if you ever restart the VM server, the Docker Engine will automatically spin up KingBot and the Postgres database the instant the machine turns back on! You won't need to manually start it.

---

## Phase 5: Post-Setup Maintenance & Updates

Once your VM is running, you will occasionally need to update the code, check the bot's health, or free up disk space. Run these commands from inside the `~/KingBot` folder.

### 🔄 1. Updating KingBot with New Code
When you write new code on your Windows PC, push it to GitHub, then pull it down to the VM to update the live bot seamlessly:
```bash
# Pull the latest changes from GitHub
git pull origin master

# Clean up leftover broken containers and completely rebuild the live code
docker compose up -d --build --remove-orphans
```
*(You do not need to stop the bot first. Docker automatically hot-swaps the container without dropping your database!)*

### 📊 2. Checking Bot Health & Logs
If the bot acts weird or isn't responding, check the logs out to see the raw Python terminal output. Using `docker compose logs` prevents "No such container" errors by automatically finding the right service:
```bash
# View the live, scrolling terminal logs for the bot
docker compose logs -f kingbot-app

# View the last 50 lines of logs (good for a quick check)
docker compose logs --tail 50 kingbot-app

# View the live logs for the Postgres Database
docker compose logs -f postgres
```
*(Press `Ctrl+C` to exit the live log view)*

### 🛑 3. Restarting and Stopping Containers
```bash
# Quickly restart just the Python bot (keeps database running)
docker compose restart kingbot-app

# Completely restart EVERYTHING (bot, database, message queue)
docker compose restart

# Turn off the entire operation cleanly
docker compose down
```

### 🧹 4. Freeing Up Disk Space
Over time, Docker will hoard old image versions from your previous code updates. Run this to clear out unused data and free up disk space on the VM:
```bash
docker image prune -a -f
```

### 💣 5. The Nuclear Option (Start from Scratch)
If you completely broke the database or want to wipe the slate perfectly clean (including all saved data):
```bash
docker compose down -v
```
*(Warning: This deletes your Postgres volume data!)*
