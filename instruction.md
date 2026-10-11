# SWS405 – Assignment 2 – Lab 1 "Beginner's Luck": Step-by-Step Instructions

> **What this file is:** a walkthrough of *what to run*, *what to look for*, and *when to take a screenshot* for MemLabs Lab 1 on Kali Linux.
> It deliberately does **not** give you the flag values or write your reasoning paragraphs. The assignment says the investigation log and the explanations must be your own work, and you lose marks if you copy them. Find the flags yourself and explain them in your own words.
>
> **Deadline:** 12 October 2026, 4:00 PM BST. Lab 1 is worth **2 marks**: about 40% for the flags and screenshots, 35% for the investigation log, and 25% for forensic reasoning.

---

## 0. Screenshot rules (read this first)

The assignment says that **unlabeled or unexplained screenshots earn no marks**, even if the flag is correct. So for every screenshot:

1. **Name the file** using the pattern `L1-<number>_<what>.png` (for example `L1-05_consoles_base64.png`). Save them all in `~/memlabs/Lab1/screenshots/`.
2. **Make sure the screenshot shows the command and its output together.** Don't crop out the command line.
3. **Put a caption under it in the report:** *"Figure L1-05: Output of `consoles` showing an encoded string in cmd.exe's console history."*
4. Your terminal prompt should show **your name or student ID** so the screenshots are clearly yours (see Step 1.4).

Taking screenshots in Kali:
- Press `PrtSc` for the full screen, or `Shift+PrtSc` to select an area.
- Or run `xfce4-screenshooter -r` for a region, or install Flameshot: `sudo apt install flameshot`, then `flameshot gui`.

Every place you need a screenshot is marked like this: **📸 SCREENSHOT L1-xx**

---

## 1. One-time setup

### 1.1 Create the working folders
```bash
mkdir -p ~/memlabs/Lab1/{dump,screenshots,notes}
cd ~/memlabs/Lab1
```

### 1.2 Copy the memory image into Kali
Your image is currently at `C:\Users\HP\OneDrive\Desktop\SWS405\MemLabs-Lab1\MemoryDump_Lab1.raw` (about 1 GB). Get it into `~/memlabs/Lab1/` using one of these:
- **VirtualBox or VMware shared folder:** mount it, then `cp /media/sf_<share>/MemoryDump_Lab1.raw ~/memlabs/Lab1/`
- **USB drive:** copy the file onto it and drag it into the folder.
- **Download it again inside Kali:** use the link in the Lab 1 README on github.com/stuxnet999/MemLabs, then extract it with `7z x MemLabs-Lab1.7z`.

### 1.3 Hash the evidence before you touch it (good forensic practice)
```bash
md5sum MemoryDump_Lab1.raw
sha256sum MemoryDump_Lab1.raw
```
**📸 SCREENSHOT L1-01_evidence_hash.** This shows you checked the integrity of the evidence before analysing it. Mention it in your report.

### 1.4 Put your identity in the prompt and record the whole session
> **Haven't installed Volatility yet?** Do **Step 1.5** first, then come back here.

Make sure Step 1.1 is done first, because the `notes` folder must exist. Then:
```bash
cd ~/memlabs/Lab1
script -a ~/memlabs/Lab1/notes/lab1_session.log
# --- now INSIDE the recording ---
PROMPT='[%n@<YOUR_STUDENT_ID> %1~]$ '        # zsh (Kali default). In bash: PS1='[\u@<ID> \W]\$ '
date; whoami
```
Set the prompt *after* starting `script`, because `script` opens a new shell that would reset it.
`script` records **every command and its output** into `lab1_session.log`, including dead ends. That file becomes your **investigation log** (worth 35%). When you finish the lab, type `exit` to stop recording.

### 1.5 Install the tools (do this BEFORE Step 1.4's `script` command, or inside it to log it)

**A. Update Kali and install the helper tools**
```bash
sudo apt update
sudo apt install -y wget unzip p7zip-full unrar gimp ghex steghide git binutils
```
(`binutils` provides `strings`.) If `unrar` isn't found, skip it and use `7z` instead. It can open RAR files too.

**B. Try the method from the assignment PDF (Option A)**
```bash
sudo apt install -y volatility
```
- If it installs, test it with `volatility --info | head -20`. If that works, run `alias vol='volatility'` and go to **D**.
- If you get `E: Unable to locate package volatility` (normal on new Kali, where Volatility 2 was removed), **take a screenshot of the error** (dead end for your log) and go to **C**.

**C. Install the Volatility 2.6 standalone binary (recommended fallback)**

This is one self-contained Linux program with Python 2 and all the plugins built in, so it needs no Python 2 install.
```bash
cd ~
wget https://github.com/volatilityfoundation/volatility/releases/download/2.6.1/volatility_2.6_lin64_standalone.zip
# (mirror if GitHub fails: https://downloads.volatilityfoundation.org/releases/2.6/volatility_2.6_lin64_standalone.zip)
unzip volatility_2.6_lin64_standalone.zip
ls volatility_2.6_lin64_standalone/
chmod +x volatility_2.6_lin64_standalone/volatility_2.6_lin64_standalone
```
Make the `vol` shortcut permanent (Kali uses zsh by default):
```bash
echo "alias vol='$HOME/volatility_2.6_lin64_standalone/volatility_2.6_lin64_standalone'" >> ~/.zshrc
source ~/.zshrc
```
(If your shell is bash, use `~/.bashrc` instead. Check with `echo $SHELL`.)

**D. Verify**
```bash
vol --info | head -20
vol --info | grep Win7SP1x64
```
You should see the Volatility banner and `Win7SP1x64` listed as a profile.

**📸 SCREENSHOT L1-02_volatility_installed.** Show `vol --info` working.

**E. Community plugins (not needed for Lab 1, but do it now for Lab 2)**
```bash
cd ~ && git clone https://github.com/superponible/volatility-plugins.git
```

> In your report, write down which install option you used and why. If `apt install volatility` failed, that is a documented dead end, so include it.

| Install problem | Fix |
|---|---|
| `Unable to locate package volatility` | Expected on new Kali. Use **C**. |
| `wget: command not found` | `sudo apt install wget` |
| `Permission denied` when running vol | You skipped `chmod +x`. Run it again. |
| `vol: command not found` | Run `source ~/.zshrc`, or open a new terminal. |
| Very slow or out of memory | Give the Kali VM at least 4 GB RAM and ~5 GB free disk (the image is 1 GB, plus dumps). |

---

## 2. Investigation

All commands below assume you are in `~/memlabs/Lab1` and that the `vol` alias is set. To save typing, set:
```bash
IMG=MemoryDump_Lab1.raw
```

### Step 2.1 – Identify the profile (Part B, item 1)
```bash
vol -f $IMG imageinfo
```
This takes 1–3 minutes. Look at the **"Suggested Profile(s)"** line and use the **first** profile it suggests from now on. Then set:
```bash
P=<first_suggested_profile>      # e.g. Win7SP1x64
```
**📸 SCREENSHOT L1-03_imageinfo.** Show the suggested profiles and the image date/time.

Note for your report: what OS is it, and what was the **image date/time**, which tells you when the memory was captured?

### Step 2.2 – List the processes (Guidance Q1)
```bash
vol -f $IMG --profile=$P pslist
vol -f $IMG --profile=$P pstree
```
**📸 SCREENSHOT L1-04a_pslist** and **📸 SCREENSHOT L1-04b_pstree**

Go through the list and sort the processes into two groups:
- **System processes:** `System`, `smss.exe`, `csrss.exe`, `wininit.exe`, `services.exe`, `lsass.exe`, `svchost.exe`, `explorer.exe`, and so on.
- **User applications:** look for **a command prompt**, **a paint program**, and **an archive manager**. Write down their **PIDs**, because you will need them later.
- **A forensic tool:** one process is the tool that *captured* this memory dump. Its name gives it away. Say in the report why it's not part of the user's activity.

Use `pstree` to see which processes were launched from `explorer.exe`, meaning the user started them by hand.

---

### 🚩 FLAG 1 – Console history

### Step 2.3 – Try `cmdscan` first
```bash
vol -f $IMG --profile=$P cmdscan
```
**📸 SCREENSHOT L1-05a_cmdscan.** Note what it shows: the command the user typed. Does it show what the command *printed*? It doesn't, so this is a partial result and goes in your log.

### Step 2.4 – Use `consoles`
```bash
vol -f $IMG --profile=$P consoles
```
Look at the **screen buffer** of the `cmd.exe` / `conhost.exe` entry. You'll see an output string that looks like **Base64**: letters, digits, `+` and `/`, often ending in `=`.

**📸 SCREENSHOT L1-05b_consoles_encoded.** Highlight or circle the encoded string.

### Step 2.5 – Decode it
```bash
echo '<paste_the_string_here>' | base64 -d ; echo
```
**📸 SCREENSHOT L1-06_FLAG1_decoded.** This is **Flag 1**. Label it clearly.

Question for your report: why did `consoles` show something that `cmdscan` didn't? Hint: one reads the *command history buffer*, while the other reads the *console screen buffer* held in `conhost.exe`.

---

### 🚩 FLAG 2 (the archive) – Archive manager + password hashes

> MemLabs numbers this one as the "3rd stage". Number the flags in your report by the order **you** found them, and say which stage each one is.

### Step 2.6 – See what file the archive manager had open
```bash
vol -f $IMG --profile=$P cmdline -p <archive_manager_PID>
```
This shows the **full path of the archive** passed to the program. Write it down.

**📸 SCREENSHOT L1-07_cmdline_archive.**

### Step 2.7 – Find the archive in memory
```bash
vol -f $IMG --profile=$P filescan > notes/filescan.txt
grep -i "\.rar" notes/filescan.txt
grep -i "<archive_name>" notes/filescan.txt
```
Note the **physical offset**, which is the first column (e.g. `0x000000003f......`). You may see several entries for the same file, and any of them may work.

**📸 SCREENSHOT L1-08_filescan_grep.**

### Step 2.8 – Extract it
```bash
vol -f $IMG --profile=$P dumpfiles -Q <offset> -D dump/
ls -la dump/
file dump/*
```
Rename the file you get (it'll be named something like `file.None.0x....dat`):
```bash
cp dump/file.None.<...>.dat dump/Important.rar
```
**📸 SCREENSHOT L1-09_dumpfiles_rar.** Show the dump command plus the `file` output confirming it's a RAR archive.

### Step 2.9 – Try to open it
```bash
unrar l dump/Important.rar
unrar x dump/Important.rar dump/
```
It asks for a password, and the archive's **comment tells you what the password is supposed to be**. Read it carefully, including **which account** and **upper or lower case**.

**📸 SCREENSHOT L1-10_rar_password_hint.** Show the comment or hint text.

### Step 2.10 – Recover the password hashes from memory
```bash
vol -f $IMG --profile=$P hashdump
```
The output format is `user:RID:LM_hash:NTLM_hash:::`. The **NTLM hash is the 4th field**. Find the line for the account the hint mentioned.

**📸 SCREENSHOT L1-11_hashdump.**

Convert the hash to the case the hint asked for:
```bash
echo '<ntlm_hash>' | tr 'a-z' 'A-Z'
```

### Step 2.11 – Extract the archive
```bash
unrar x -p<HASH_IN_CORRECT_CASE> dump/Important.rar dump/
# or: 7z x -p<HASH_IN_CORRECT_CASE> dump/Important.rar -odump/
ls -la dump/
xdg-open dump/<extracted_image>.png
```
**📸 SCREENSHOT L1-12_rar_extracted.** Show the extraction command succeeding.
**📸 SCREENSHOT L1-13_FLAG_archive.** Show the opened image with the flag visible. Label it as the flag from the archive.

> If the first password attempt fails (e.g. you tried lowercase), **keep that in your log**. It shows a real investigation.

---

### 🚩 FLAG 3 (the drawing) – Paint process memory

### Step 2.12 – Dead end first: look for an image file
```bash
grep -iE "\.(png|bmp|jpg)" notes/filescan.txt
```
Note whether you found a saved drawing. You won't find one, because the user hadn't saved it yet, so the drawing only exists in the **paint process's memory**. Record this in your log as the reason you dump the process instead.

### Step 2.13 – Dump the paint process memory
```bash
vol -f $IMG --profile=$P memdump -p <paint_PID> -D dump/
ls -la dump/*.dmp
```
**📸 SCREENSHOT L1-14_memdump_paint.**

### Step 2.14 – (Optional dead end) look for strings or signatures
```bash
strings dump/<paint_PID>.dmp | grep -i "flag{"
```
You'll probably get nothing useful, because the drawing is stored as **raw pixels** and not as text. Log it anyway; it explains why you moved on to raw image viewing.

### Step 2.15 – View the raw memory as an image in GIMP
```bash
cp dump/<paint_PID>.dmp dump/<paint_PID>.data
gimp dump/<paint_PID>.data &
```
In GIMP's **"Load Image from Raw Data"** dialog:
1. **Image Type:** `RGB Alpha`
2. **Width:** start with your screen resolution width, e.g. `1280`. Try `1920` or `1366` if the image looks diagonal or smeared. Diagonal stripes mean the width is wrong.
3. **Height:** around `1024`, or any value large enough.
4. **Offset:** drag the slider slowly through the file and watch the preview. Most of it is noise, but at some offset you'll see clear shapes and handwritten-looking text. Fine-tune the **Width** until the text is straight.
5. Click **Open**.

The text will probably appear **upside down or mirrored**. Fix it with **Image → Transform → Flip Vertically**, and/or **Rotate 180°** / **Flip Horizontally**.

**📸 SCREENSHOT L1-15_gimp_raw_settings.** Show the dialog with the offset, width and height values visible.
**📸 SCREENSHOT L1-16_FLAG_paint.** Show the flipped image with the flag readable. Write down the exact Width and Offset values you used.

---

### Step 2.16 – Rest of the Part B checklist (for completeness of the log)
Run these quickly and record what you found, even if it's "nothing relevant":
```bash
vol -f $IMG --profile=$P envars | grep -iE "flag|pass|key"
vol -f $IMG --profile=$P iehistory
```
**📸 SCREENSHOT L1-17_checklist_other** (optional). Documented dead ends earn credit in the log.

### Step 2.17 – Stop recording
```bash
exit        # ends the `script` session; log saved to notes/lab1_session.log
```

---

## 3. Screenshot checklist

| # | Filename | Shows | Required? |
|---|----------|-------|-----------|
| 01 | `L1-01_evidence_hash.png` | md5/sha256 of image | Recommended |
| 02 | `L1-02_volatility_installed.png` | `vol --info` working | Recommended |
| 03 | `L1-03_imageinfo.png` | Profile + capture time | **Yes** |
| 04a/b | `L1-04a_pslist.png`, `L1-04b_pstree.png` | Process list | **Yes** |
| 05a | `L1-05a_cmdscan.png` | Command typed | **Yes** |
| 05b | `L1-05b_consoles_encoded.png` | Encoded string | **Yes** |
| 06 | `L1-06_FLAG1_decoded.png` | **Flag 1** | **Yes** |
| 07 | `L1-07_cmdline_archive.png` | Archive path | **Yes** |
| 08 | `L1-08_filescan_grep.png` | Archive offset | **Yes** |
| 09 | `L1-09_dumpfiles_rar.png` | Extracted RAR | **Yes** |
| 10 | `L1-10_rar_password_hint.png` | Password hint | **Yes** |
| 11 | `L1-11_hashdump.png` | NTLM hashes | **Yes** |
| 12 | `L1-12_rar_extracted.png` | Successful unrar | **Yes** |
| 13 | `L1-13_FLAG_archive.png` | **Archive flag** | **Yes** |
| 14 | `L1-14_memdump_paint.png` | Process dump | **Yes** |
| 15 | `L1-15_gimp_raw_settings.png` | GIMP raw settings | **Yes** |
| 16 | `L1-16_FLAG_paint.png` | **Paint flag** | **Yes** |
| 17 | `L1-17_checklist_other.png` | envars / iehistory | Optional |

---

## 4. Report template for Lab 1 (fill this in yourself)

Copy this into your Word document or report file and replace everything in `< >` **in your own words**.

```markdown
# Lab 1 — Beginner's Luck

**Student:** <name>   **Student ID:** <id>   **Date:** <date>
**Environment:** Kali Linux <version>, Volatility <version / install option used>
**Evidence:** MemoryDump_Lab1.raw — MD5: <...>  SHA256: <...>

## 1. Summary
<2–3 sentences: what the scenario was, what you found, how many flags.>

## 2. Flags found
| # | Flag | Plugin / technique | Figure |
|---|------|--------------------|--------|
| 1 | <flag> | <plugin(s)> | L1-06 |
| 2 | <flag> | <plugin(s)> | L1-13 |
| 3 | <flag> | <plugin(s)> | L1-16 |

## 3. Investigation log
<Step-by-step: command → what you saw → what you decided next.
 Include dead ends (e.g. cmdscan only partial, strings on paint dump found nothing,
 any wrong password attempt, apt install failing). Paste key lines from
 notes/lab1_session.log and refer to figures.>

### 3.1 Scoping (imageinfo, pslist, pstree)   — Fig L1-03, L1-04
### 3.2 Flag 1 — console history               — Fig L1-05a, L1-05b, L1-06
### 3.3 Archive flag — WinRAR + hashdump       — Fig L1-07 … L1-13
### 3.4 Paint flag — process memory            — Fig L1-14 … L1-16
### 3.5 Other checks (envars, iehistory)       — Fig L1-17

## 4. Forensic reasoning (3–5 sentences, at least 2 flags)
<Explain WHY each plugin was the right tool. Questions to answer for yourself:
 - Why does console output survive in RAM, and why `consoles` and not just `cmdscan`?
 - Why can a file be extracted from memory with filescan+dumpfiles even though
   you never had the disk? (file objects / cached pages in RAM)
 - Why can hashdump recover password hashes from RAM? (SAM/SYSTEM registry hives
   loaded in memory)
 - Why did the drawing only exist in mspaint's process memory, and why does
   viewing it as raw RGBA pixels work when strings/grep did not?>

## 5. Conclusion
<One sentence per flag connecting: plugin → artifact → what it proved.>

## 6. Figures
<Insert every screenshot with its label "Figure L1-xx: <caption>".>
```

---

## 5. Common problems

| Problem | Fix |
|---------|-----|
| `imageinfo` is very slow | That's normal (1–3 min). Or use `vol -f $IMG kdbgscan`. |
| `No suitable address space mapping found` | You used the wrong profile. Re-check `imageinfo`. |
| `dumpfiles` creates no file | Try another offset from the `filescan` results, and make sure the `-D dump/` folder exists. |
| `unrar: command not found` | `sudo apt install unrar`, or use `7z x -p<pw> file.rar`. |
| Wrong RAR password | Check the case (UPPER/lower) and that you used the **NTLM** hash (4th field), not the LM hash. |
| GIMP image is diagonal stripes | The width is wrong. Change it a little at a time until the lines straighten. |
| GIMP doesn't show the raw dialog | Make sure the file extension is `.data`, or choose "Raw image data" under *Select File Type* in the Open dialog. |
| Alias lost after closing the terminal | Add the `alias vol=...` line to `~/.zshrc` and run `source ~/.zshrc`. |

---
---

# LAB 2 – "A New World": Step-by-Step Instructions

> **Worth 2 marks. There are 3 flags.** One of them needs a flag you found in Lab 1 (the one inside `flag3.png`).
> As in Lab 1, this guide tells you **what to run, what you should see, and when to take a screenshot**. It doesn't give you the flag values.
>
> ⚠️ **About placeholders:** in Lab 1 some commands failed because placeholders like `<offset>` were typed literally. In this lab, most commands **save values into shell variables for you** (e.g. `OFF=$(...)`), so you can copy and paste them as they are. Anything still written in `CAPITALS_LIKE_THIS` must be replaced with your own value, and **never type `< >`**.

Screenshot names use the pattern `L2-xx_<what>.png`, saved in `~/memlabs/Lab2/screenshots/`.

---

## L2-0. Get the files and set up

### L2-0.1 Download the Lab 2 memory image
1. Open https://github.com/stuxnet999/MemLabs in Kali's browser, then go to **Lab 2**.
2. Download the archive from the link in that README.
3. Set up the folder and extract the archive:
```bash
mkdir -p ~/memlabs/Lab2/{dump,screenshots,notes}
mv ~/Downloads/MemLabs-Lab2.7z ~/memlabs/Lab2/      # use the real downloaded file name
cd ~/memlabs/Lab2
7z x MemLabs-Lab2.7z
ls -lh
```
**Expected outcome:** you see `MemoryDump_Lab2.raw` (about 2 GB).

### L2-0.2 Install the extra tools for this lab
```bash
sudo apt install -y keepassxc sqlite3
```
- `keepassxc` opens KeePass password databases (`.kdbx`).
- `sqlite3` reads the Chrome history database (used in the fallback method).

Make sure the community plugin pack is there:
```bash
ls ~/volatility-plugins/ | grep -i chrome
```
**Expected outcome:** `chromehistory.py` appears in the list. If it doesn't:
```bash
cd ~ && git clone https://github.com/superponible/volatility-plugins.git && cd ~/memlabs/Lab2
```

### L2-0.3 Start recording and set variables
Run these **every time** you start a new recording:
```bash
cd ~/memlabs/Lab2
script -a ~/memlabs/Lab2/notes/lab2_session.log
PROMPT='[%n@02230297 %1~]$ '
IMG=MemoryDump_Lab2.raw
date; whoami
```

### L2-0.4 Hash the evidence
```bash
md5sum $IMG
sha256sum $IMG
```
**📸 SCREENSHOT L2-01_evidence_hash**

---

## L2-1. Scope the image (Guidance Q1)

### L2-1.1 Profile
```bash
vol -f $IMG imageinfo
```
**Expected outcome:** `Suggested Profile(s)` with **Win7SP1x64** first. Then set:
```bash
P=Win7SP1x64
```
(If the first suggestion is different, use that instead.)

**📸 SCREENSHOT L2-02_imageinfo**

### L2-1.2 Processes
```bash
vol -f $IMG --profile=$P pslist | tee notes/pslist.txt
vol -f $IMG --profile=$P pstree | tee notes/pstree.txt
```
**📸 SCREENSHOT L2-03a_pslist** and **📸 L2-03b_pstree**

Then filter for the two applications the guidance talks about:
```bash
grep -iE "chrome|keepass" notes/pslist.txt
```
**Expected outcome:**
- **Several `chrome.exe` processes.** This is normal, because Chrome runs one process per tab or extension. This is the **browsing session**.
- **One `KeePass.exe` process.** This is the **password manager**.

**📸 SCREENSHOT L2-03c_chrome_keepass**

---

## 🚩 L2 FLAG 1 – Environment variables (Guidance Q2)

### L2-2.1 Dump all environment variables to a file
```bash
vol -f $IMG --profile=$P envars > notes/envars.txt
wc -l notes/envars.txt
```
The output is long, because every process has around 30–50 variables.

### L2-2.2 Find the odd one out
Normal Windows variables are things like `PATH`, `TEMP`, `TMP`, `USERNAME`, `windir` and `COMPUTERNAME`. List the **variable names** with how often each appears, so you can spot one that isn't standard:
```bash
awk '{print $4}' notes/envars.txt | sort | uniq -c | sort -n
```
**Expected outcome:** one variable name that **is not a normal Windows variable**. It looks like a modified version of a normal temp variable.

Look at its value:
```bash
grep -i "VARIABLE_NAME_YOU_FOUND" notes/envars.txt | head -5
```
**Expected outcome:** the value looks like a Windows path that ends in a long **Base64-looking** string (letters and digits, no spaces).

**📸 SCREENSHOT L2-04_envars_suspicious.** Highlight the variable.

### L2-2.3 Decode it
Copy **only the Base64 part**, which is everything after the last `\`:
```bash
echo 'PASTE_BASE64_PART_HERE' | base64 -d ; echo
```
**Expected outcome:** a readable `flag{...}`. This is **Lab 2 Flag 1**.

**📸 SCREENSHOT L2-05_FLAG1_decoded**

> If `base64 -d` says `invalid input`, add `=` or `==` at the end and try again. Base64 length must be a multiple of 4.

**Reasoning point for the report:** every process keeps its own copy of the environment variables in its memory (in the PEB, the Process Environment Block). `envars` reads them for every process, so a hidden value shows up even though nothing printed it on screen.

---

## 🚩 L2 FLAG 2 – KeePass database (Guidance Q3)

### L2-3.1 Scan files and find the database
```bash
vol -f $IMG --profile=$P filescan > notes/filescan.txt
grep -i "\.kdbx" notes/filescan.txt
```
**Expected outcome:** a line with a `.kdbx` file (KeePass 2 database) in a user's folder. Note the **folder name** it's in.

**📸 SCREENSHOT L2-06_filescan_kdbx**

### L2-3.2 Look at what else is in that folder
The guidance says the master password is not stored as plain text next to the database. List the other files in the **same folder**:
```bash
grep -i "FOLDER_NAME_FROM_ABOVE" notes/filescan.txt
grep -i "password" notes/filescan.txt
```
**Expected outcome:** besides the `.kdbx`, there's an **image file** with a password-related name in the same folder. That's where the master password is hiding.

**📸 SCREENSHOT L2-07_filescan_password_file**

### L2-3.3 Dump both files
Dump the database:
```bash
OFF=$(grep -i "\.kdbx" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/
```
Dump the password image (change `password.png` if your file has a different name):
```bash
OFF=$(grep -i "password.png" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/
ls -la dump/
file dump/*
```
**Expected outcome:** `file` reports one file as **Keepass password database 2.x KDBX** and one as **PNG image data**.

Rename them. Use the real `file.None.0x....dat` names that `ls` shows; type `dump/file` and press **Tab** to complete:
```bash
cp dump/file.None.0xKDBX_ONE.dat dump/Hidden.kdbx
cp dump/file.None.0xPNG_ONE.dat dump/Password.png
file dump/Hidden.kdbx dump/Password.png
```
**📸 SCREENSHOT L2-08_dumpfiles_kdbx_png**

> If `dumpfiles` creates nothing, try another offset for the same file (filescan may list several). That's a dead end to log.

### L2-3.4 Read the master password from the image
```bash
xdg-open dump/Password.png
```
**Expected outcome:** a picture whose main content is a distraction. The actual password is written **small, in a corner**. Zoom in and check **every corner**, especially the **bottom-right**.

Write the password down exactly. Watch for upper/lower case, `0` vs `O`, and `_`.

**📸 SCREENSHOT L2-09_master_password_image.** Zoom in so the password is readable.

### L2-3.5 (Part B checklist) – hashdump as a cross-check
```bash
vol -f $IMG --profile=$P hashdump
```
**Expected outcome:** Windows account NTLM hashes. These are **not** the KeePass master password, because KeePass uses its own password, separate from Windows. Note in your log that you checked this and why it didn't apply. **📸 L2-10_hashdump (optional)**

### L2-3.6 Open the database
**Option A – Command line (easy to screenshot, recommended):**
```bash
keepassxc-cli ls dump/Hidden.kdbx
```
Enter the master password when asked.

**Expected outcome:** a list of entries and groups, including **`Recycle Bin/`**.
```bash
keepassxc-cli ls dump/Hidden.kdbx "Recycle Bin"
```
**Expected outcome:** one or more entries inside the Recycle Bin. These were "deleted", but they're still stored in the database.

Show the entry **with its hidden password** (`-s` = show protected fields):
```bash
keepassxc-cli show -s dump/Hidden.kdbx "Recycle Bin/ENTRY_NAME"
```
**Expected outcome:** the `Password:` field contains a `flag{...}`. This is **Lab 2 Flag 2**.

**Option B – GUI:**
```bash
keepassxc dump/Hidden.kdbx &
```
Enter the master password → click **Recycle Bin** on the left → double-click the entry → click the 👁 **eye icon** next to Password.

**📸 SCREENSHOT L2-11_keepass_opened** (database unlocked, entry list visible)
**📸 SCREENSHOT L2-12_FLAG2_recyclebin** (Recycle Bin entry with the password shown)

> If KeePassXC says the database is corrupt, dump it again from another filescan offset. If it says invalid credentials, re-check the password character by character. Log each attempt.

**Reasoning point for the report:** KeePass "deletes" entries by moving them to the Recycle Bin group **inside the same encrypted file**, so they aren't really gone. The database was cached in RAM because KeePass had it open, which is why `filescan` and `dumpfiles` could recover it.

---

## 🚩 L2 FLAG 3 – Chrome history + Lab 1 flag (Guidance Q4)

### L2-4.1 Read Chrome history with the community plugin
`--plugins=` must come **first**, before `-f`:
```bash
vol --plugins=$HOME/volatility-plugins -f $IMG --profile=$P chromehistory > notes/chromehistory.txt
wc -l notes/chromehistory.txt
grep -iE "mega|drive.google|dropbox|mediafire" notes/chromehistory.txt
```
**Expected outcome:** a table of URLs, one of which is a **`mega.nz`** link (a file-sharing service).

**📸 SCREENSHOT L2-13_chromehistory_link**

**If `chromehistory` fails** (plugin not found, or Python errors with the standalone binary), record the error in your log and use a fallback:

**Fallback 1 – dump Chrome's History database and read it with sqlite3:**
```bash
grep -iE 'Chrome.*Default.History$' notes/filescan.txt
OFF=$(grep -iE 'Chrome.*Default.History$' notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/
ls -lt dump/ | head
cp dump/file.None.0xNEWEST_ONE.dat dump/History
sqlite3 dump/History "SELECT url, title FROM urls;"
```

**Fallback 2 – search Chrome's process memory for the URL:**
```bash
for pid in $(grep -i chrome notes/pslist.txt | awk '{print $3}'); do vol -f $IMG --profile=$P memdump -p $pid -D dump/; done
strings dump/*.dmp | grep -oiE "https?://mega\.nz/[^ \"'<>]*" | sort -u
```

### L2-4.2 Download the file
1. Copy the full `mega.nz` link (including the part after `#`) and open it in Kali's browser.
2. Download the file. You should get **`Important.zip`**.
3. Move it into your lab folder:
```bash
mv ~/Downloads/Important.zip ~/memlabs/Lab2/dump/
```
**📸 SCREENSHOT L2-14_mega_download** (browser page showing the file)

> If the Mega link no longer works, screenshot the error, record it in your log, and tell your tutor. Don't use another student's file.

### L2-4.3 Read the instructions bundled with the file
```bash
unzip -l dump/Important.zip
```
**Expected outcome:** a **zip comment** at the top explaining **how to make the password**:
- **which hash function** to use
- **which flag from which lab** to hash
- **upper or lower case**

**📸 SCREENSHOT L2-15_zip_password_hint**

### L2-4.4 Make the password from your Lab 1 flag
The hint refers to the Lab 1 **"stage 3"** flag. That's the flag inside **`flag3.png`**, which your Lab 1 report calls **Flag 2**.

Use `echo -n` so no newline is added. Without `-n` you get a completely different hash. Save the result in a variable to avoid copy mistakes:
```bash
PW=$(echo -n 'PASTE_YOUR_LAB1_FLAG3_HERE' | sha1sum | awk '{print $1}'); echo $PW
```
- Replace `sha1sum` with `md5sum` or `sha256sum` if the hint names a different hash.
- `sha1sum` output is already **lowercase**. If the hint says uppercase, use `PW=$(echo $PW | tr 'a-z' 'A-Z')`.
- Hash the **whole** flag including `flag{` and `}`, unless the hint says otherwise.

**📸 SCREENSHOT L2-16_password_derivation**

### L2-4.5 Extract the archive
```bash
unzip -P "$PW" dump/Important.zip -d dump/
```
If `unzip` says `unsupported compression method 99` (AES encryption), use 7z:
```bash
7z x -p"$PW" dump/Important.zip -odump/
```
**Expected outcome:** an image file is extracted.
```bash
ls -la dump/
xdg-open dump/Important.png      # use the real name shown by ls
```
**📸 SCREENSHOT L2-17_zip_extracted**
**📸 SCREENSHOT L2-18_FLAG3_image.** The flag must be readable. This is **Lab 2 Flag 3**.

> If you get a wrong password, check: `-n` in echo, the right Lab 1 flag (from `flag3.png`), the right hash function and case. Log every attempt.

### L2-4.6 Stop recording
```bash
exit
```

---

## L2 Screenshot checklist

| # | Filename | Shows |
|---|----------|-------|
| 01 | `L2-01_evidence_hash.png` | md5/sha256 of image |
| 02 | `L2-02_imageinfo.png` | Profile |
| 03a/b/c | `L2-03a_pslist.png`, `L2-03b_pstree.png`, `L2-03c_chrome_keepass.png` | Processes |
| 04 | `L2-04_envars_suspicious.png` | Odd environment variable |
| 05 | `L2-05_FLAG1_decoded.png` | **Flag 1** |
| 06 | `L2-06_filescan_kdbx.png` | .kdbx found |
| 07 | `L2-07_filescan_password_file.png` | Password image found |
| 08 | `L2-08_dumpfiles_kdbx_png.png` | Both files dumped + `file` output |
| 09 | `L2-09_master_password_image.png` | Master password in the image |
| 10 | `L2-10_hashdump.png` | (optional) cross-check |
| 11 | `L2-11_keepass_opened.png` | Database unlocked |
| 12 | `L2-12_FLAG2_recyclebin.png` | **Flag 2** |
| 13 | `L2-13_chromehistory_link.png` | mega.nz link |
| 14 | `L2-14_mega_download.png` | Download page |
| 15 | `L2-15_zip_password_hint.png` | Zip comment / hint |
| 16 | `L2-16_password_derivation.png` | Hash of the Lab 1 flag |
| 17 | `L2-17_zip_extracted.png` | Successful extraction |
| 18 | `L2-18_FLAG3_image.png` | **Flag 3** |

---

## L2 What to write in the report

1. **Flags table:** 3 flags, the plugin used for each, and figure numbers.
2. **Investigation log:** every command, including failures (e.g. `chromehistory` errors, wrong offsets, wrong password attempts).
3. **Required paragraph – password derivation:** in your own words, say
   - which Lab 1 flag you used (the stage-3 flag from `flag3.png`),
   - the **exact** transformation: the hash function from the zip comment, the case, and that you hashed the exact flag text with no newline (`echo -n`),
   - why `-n` matters: a newline changes the input, so the hash comes out completely different.
4. **Forensic reasoning:**
   - `envars` showed the hidden value because it's stored in each process's PEB.
   - The `.kdbx` could be recovered because it was cached in RAM while KeePass had it open.
   - The Recycle Bin entry still existed because deleting an entry moves it to another group; it doesn't erase it.
   - The community plugin was needed because Volatility 2 has no built-in Chrome parser, and `iehistory` only reads Internet Explorer/WinINet history.

## L2 Common problems

| Problem | Fix |
|---|---|
| `vol: command not found` | Run `source ~/.zshrc` |
| `The requested file doesn't exist` | `$IMG` is empty because you're in a new shell. Set the variables again (L2-0.3). |
| `chromehistory` not found | Put `--plugins=$HOME/volatility-plugins` **before** `-f`, and check the folder exists |
| `chromehistory` crashes with the standalone vol | Use Fallback 1 or 2 in L2-4.1 |
| KeePassXC "Invalid credentials" | Check the master password character by character (case, 0/O, _) |
| `unsupported compression method 99` | Use `7z x -p"$PW" ...` instead of unzip |
| Zip says wrong password | Use `echo -n`, the right Lab 1 flag, and the right hash function and case |

---
---

# LAB 3 – "The Evil's Den": Step-by-Step Instructions

> **Worth 2 marks. ONE flag, split into two halves.**
> - **First half:** a malicious Python script encoded it and saved the result in a text file. You **reverse the script's encoding**.
> - **Second half:** hidden inside a **JPEG image** using **steganography**. The passphrase is the **first half**.
>
> The flag format in this lab is **`inctf{...}`**, not `flag{...}`.
>
> ⚠️ **Placeholders:** most commands save values into variables (`OFF=$(...)`), so you can copy and paste them as they are. Anything in `CAPITALS_LIKE_THIS` needs your real value. Never type `< >`.

Screenshot names use the pattern `L3-xx_<what>.png`, saved in `~/memlabs/Lab3/screenshots/`.

---

## L3-0. Get the files and set up

### L3-0.1 Download the Lab 3 memory image
1. Open https://github.com/stuxnet999/MemLabs in Firefox, then go to **Lab 3**.
2. **Read the lab's README description carefully, especially "Note-2".** Write it down, because you'll need it for the steghide passphrase and it's worth quoting in your report. **📸 SCREENSHOT L3-00_lab3_description** (the README with the notes visible).
3. Download the archive from that page, then:
```bash
mkdir -p ~/memlabs/Lab3/{dump,screenshots,notes}
mv ~/Downloads/MemLabs-Lab3.7z ~/memlabs/Lab3/      # use the real downloaded file name
cd ~/memlabs/Lab3
7z x MemLabs-Lab3.7z
ls -lh
```
**Expected outcome:** `MemoryDump_Lab3.raw` is listed.

### L3-0.2 Tools
```bash
sudo apt install -y steghide python3
steghide --version
```

### L3-0.3 Start recording and set variables
```bash
cd ~/memlabs/Lab3
script -a ~/memlabs/Lab3/notes/lab3_session.log
PROMPT='[%n@02230297 %1~]$ '
IMG=MemoryDump_Lab3.raw
date; whoami
```

### L3-0.4 Hash the evidence
```bash
md5sum $IMG
sha256sum $IMG
```
**📸 SCREENSHOT L3-01_evidence_hash**

---

## L3-1. Scope the image

### L3-1.1 Profile – ⚠️ this one is different
```bash
vol -f $IMG imageinfo
```
**Expected outcome:** this image is **32-bit (x86)**, not x64 like Labs 1 and 2. The first suggested profile looks like **`Win7SP1x86_23418`**. Use **exactly the first one shown**:
```bash
P=Win7SP1x86_23418      # change this if your first suggestion is different
```
**📸 SCREENSHOT L3-02_imageinfo**

> If you used `Win7SP1x64` out of habit, plugins would fail or show garbage. Mention in your report that the architecture changed and why the profile matters (Volatility needs the right profile to know the layout of Windows' internal structures).

### L3-1.2 Processes
```bash
vol -f $IMG --profile=$P pslist | tee notes/pslist.txt
vol -f $IMG --profile=$P pstree | tee notes/pstree.txt
grep -i notepad notes/pslist.txt
```
**Expected outcome:** **two `notepad.exe` processes**. That's the "text-editing process" from the guidance. Note both PIDs.

**📸 SCREENSHOT L3-03a_pslist**, **📸 L3-03b_notepad_processes**

---

## 🚩 L3 FIRST HALF – The malicious script

### L3-2.1 See which files Notepad had open (Guidance Q1)
"Command-line history" in the guidance means the **command line each process was started with**, which is shown by the `cmdline` plugin:
```bash
vol -f $IMG --profile=$P cmdline | grep -i -A1 notepad
```
**Expected outcome:** two lines like `Command line : "C:\Windows\system32\NOTEPAD.EXE" "C:\Users\...\Desktop\SOMETHING"`:
- one opened a **Python script** (`.py`)
- the other opened a **text file** (`.txt`), which is the script's **output**

Write both file names down.

**📸 SCREENSHOT L3-04_cmdline_notepad**

**(Part B checklist, for the log)** Also run these and note what they show, even if it's nothing useful:
```bash
vol -f $IMG --profile=$P cmdscan
vol -f $IMG --profile=$P consoles
```

### L3-2.2 Find both files in memory
```bash
vol -f $IMG --profile=$P filescan > notes/filescan.txt
grep -iE "\.py$|\.txt$" notes/filescan.txt | grep -i desktop
```
**Expected outcome:** the `.py` script and the `.txt` output file, both on the user's Desktop. **📸 SCREENSHOT L3-05_filescan_script_txt**

Put the two file names in variables. Type the **real names** you saw, e.g. `SCRIPT=myscript.py`:
```bash
SCRIPT=SCRIPT_NAME.py
OUTTXT=OUTPUT_NAME.txt
grep -i "$SCRIPT" notes/filescan.txt
grep -i "$OUTTXT" notes/filescan.txt
```

### L3-2.3 Dump both files
Each file goes into its own folder, so you always know which `.dat` is which:
```bash
mkdir -p dump/script dump/output
OFF=$(grep -i "$SCRIPT" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/script/
OFF=$(grep -i "$OUTTXT" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/output/
ls -la dump/script dump/output
```
Copy them to their proper names (the `*.dat` matches the one dumped file in each folder):
```bash
cp dump/script/*.dat dump/$SCRIPT
cp dump/output/*.dat dump/$OUTTXT
file dump/$SCRIPT dump/$OUTTXT
```
**📸 SCREENSHOT L3-06_dumpfiles**

> If a folder is empty, try the next offset: use `sed -n 2p` instead of `head -1` in the `OFF=` line. Log it.

### L3-2.4 Read the script – DON'T run it (Guidance Q2)
```bash
cat dump/$SCRIPT
```
**📸 SCREENSHOT L3-07_script_source**

**Read it line by line and answer these in your notes. This is your report explanation:**
1. **Where does the input come from?** Look for `sys.argv[1]`. The secret was passed as a **command-line argument** when the script was run.
2. **What's the first transformation?** Look for a function that uses `^`. In Python, `^` is **XOR**. Write down the **number** each character is XORed with.
3. **What's the second transformation?** Look for `encode("base64")`. That's **Base64** encoding (Python 2 syntax).
4. **In what order are they applied?** Read the line that calls both functions. The **inner** function runs **first**.
5. **Where does the result go?** Look at the `open(..., "w")` line. It's written to the `.txt` file.

> **Why not just run it?** It's a *malicious* script from evidence. Running unknown code can damage your machine or change evidence. Analysts read and understand it first. Say this in your report.

### L3-2.5 Look at the encoded output
```bash
cat dump/$OUTTXT ; echo
```
**Expected outcome:** one line of **Base64-looking** text. **📸 SCREENSHOT L3-08_encoded_output**

### L3-2.6 Reverse it (by hand, step by step)
To reverse, undo the steps **in the opposite order**:
- The script did: **XOR first, then Base64**.
- So you do: **Base64-decode first, then XOR**. XOR with the same number undoes itself, because `(a ^ k) ^ k = a`.

**Step A – Base64-decode** (the result will look like scrambled text, which is expected):
```bash
base64 -d dump/$OUTTXT ; echo
```

**Step B – XOR every character with the key.** Replace `KEY` with the number you found in the script:
```bash
base64 -d dump/$OUTTXT | python3 -c "import sys; print(''.join(chr(b ^ KEY) for b in sys.stdin.buffer.read()))"
```
**Expected outcome:** readable text starting with **`inctf{`**. This is the **first half of the flag**. It doesn't end with `}` yet.

**📸 SCREENSHOT L3-09_FIRST_HALF**

### L3-2.7 (Recommended) Write your own reversing script
The assignment gives credit for "your own reversing script". Create `notes/reverse.py`:
```bash
nano notes/reverse.py
```
Type this in, replacing `KEY` with your number, and add your own comments explaining each line:
```python
# reverse.py - undo the transformation done by the malicious script
# Script did:  output = base64( xor(input, KEY) )
# So I do:     input  = xor( base64_decode(output), KEY )
import base64
import sys

KEY = 0  # <-- put the XOR key you found in the script here

data = open(sys.argv[1], "rb").read().strip()
decoded = base64.b64decode(data)                     # step 1: undo base64
original = "".join(chr(b ^ KEY) for b in decoded)    # step 2: undo XOR
print(original)
```
Save with `Ctrl+O`, Enter, then `Ctrl+X`. Run it:
```bash
python3 notes/reverse.py dump/$OUTTXT
```
**📸 SCREENSHOT L3-10_reverse_script** (show `cat notes/reverse.py` and the output)

Save the first half in a variable for later. Type exactly what was printed:
```bash
HALF1='inctf{...exactly what your script printed...'
echo "$HALF1"
```

---

## 🚩 L3 SECOND HALF – Steganography

### L3-3.1 Find photo files in memory (Guidance Q3)
```bash
grep -iE "\.jpe?g$|\.png$|\.bmp$|\.gif$" notes/filescan.txt
```
**Expected outcome:** a list of image files. Most are normal Windows or sample pictures (wallpapers, theme images, sample photos, etc.). **One** has a name that **doesn't fit**: it's on the user's own folder (e.g. Desktop) and its name suggests something hidden.

Narrow it down to the user's files:
```bash
grep -iE "\.jpe?g$" notes/filescan.txt | grep -iv "windows\\\\web\|sample\|program"
```
**📸 SCREENSHOT L3-11_filescan_images.** Highlight the odd one, and note in your report **why** it stands out.

### L3-3.2 Dump the suspicious image
Type its real file name:
```bash
IMGNAME=SUSPICIOUS_NAME.jpeg
mkdir -p dump/image
OFF=$(grep -i "$IMGNAME" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/image/
ls -la dump/image/
cp dump/image/*.dat dump/$IMGNAME
file dump/$IMGNAME
```
**Expected outcome:** `file` says **JPEG image data**. **📸 SCREENSHOT L3-12_dump_image**

Look at it. It looks like a normal picture, and that's the point of steganography:
```bash
xdg-open dump/$IMGNAME
```

### L3-3.3 Work out the passphrase (Guidance Q4)
Re-read **Note-2** from the Lab 3 README (screenshot L3-00). It says how the two halves are related. The natural passphrase is the **first half of the flag**, typed exactly as you recovered it.

### L3-3.4 Extract the hidden data with steghide
```bash
steghide extract -sf dump/$IMGNAME -p "$HALF1" -xf dump/secret.txt
cat dump/secret.txt ; echo
```
**Expected outcome:**
- steghide prints `wrote extracted data to "dump/secret.txt".`
- `secret.txt` contains the **second half of the flag**, ending with `}`.

**📸 SCREENSHOT L3-13_steghide_extract.** This is the screenshot the assignment specifically asks for. Show the command, the "wrote extracted data" line, and the `cat` output.

If it fails, check (and log each attempt):

| steghide error | Meaning / fix |
|---|---|
| `could not extract any data with that passphrase!` | Passphrase is wrong: check `echo "$HALF1"` character by character. Did you include `inctf{`? |
| `the file format ... is not supported` | The dump isn't a full JPEG. Try the next filescan offset (`sed -n 2p`). |
| `the file "..." does already exist. overwrite ?` | Type `y`, or delete `dump/secret.txt` first. |

### L3-3.5 Join the two halves
```bash
echo "${HALF1}$(cat dump/secret.txt)"
```
**Expected outcome:** one complete flag: `inctf{` + first half + second half + `}`, with no spaces or newlines in between.

**📸 SCREENSHOT L3-14_FULL_FLAG**

### L3-3.6 Stop recording
```bash
exit
```

---

## L3 Screenshot checklist

| # | Filename | Shows |
|---|----------|-------|
| 00 | `L3-00_lab3_description.png` | README with Note-2 |
| 01 | `L3-01_evidence_hash.png` | md5/sha256 |
| 02 | `L3-02_imageinfo.png` | **x86** profile |
| 03a/b | `L3-03a_pslist.png`, `L3-03b_notepad_processes.png` | Two notepad.exe |
| 04 | `L3-04_cmdline_notepad.png` | Files opened in Notepad |
| 05 | `L3-05_filescan_script_txt.png` | Script + output in filescan |
| 06 | `L3-06_dumpfiles.png` | Both files extracted |
| 07 | `L3-07_script_source.png` | Malicious script code |
| 08 | `L3-08_encoded_output.png` | Encoded text file |
| 09 | `L3-09_FIRST_HALF.png` | **First half** decoded |
| 10 | `L3-10_reverse_script.png` | Your reversing script + output |
| 11 | `L3-11_filescan_images.png` | Odd image file highlighted |
| 12 | `L3-12_dump_image.png` | JPEG extracted |
| 13 | `L3-13_steghide_extract.png` | **Second half** – steghide |
| 14 | `L3-14_FULL_FLAG.png` | **Complete flag** |

---

## L3 What to write in the report

1. **Complete flag** with the steghide screenshot (L3-13) and the full-flag screenshot (L3-14).
2. **Required explanation – the script's transformation**, in your own words:
   - the input came from `sys.argv[1]` (a command-line argument),
   - each character was **XORed with the key** you found, **then Base64-encoded**, and written to the `.txt` file,
   - you reversed it by **Base64-decoding first, then XORing with the same key**, because XOR is its own inverse (`(a ^ k) ^ k = a`) and the steps must be undone in reverse order,
   - include your `reverse.py` (or the one-liner) in the report.
3. **Steganography part:** why that image stood out, why the first half was the passphrase (quote Note-2), and what steghide does (it hides data inside the image's pixel/DCT data without visibly changing the picture, protected by a passphrase).
4. **Investigation log:** all commands, including the profile change to x86, cmdscan/consoles results, wrong offsets, and failed steghide attempts.
5. **Forensic reasoning:** `cmdline` reveals what a process was started with, which tells you what file Notepad had open. `filescan` + `dumpfiles` recover the files because they were cached in RAM. You read the script instead of running it, so you didn't execute malicious code or alter evidence.

## L3 Common problems

| Problem | Fix |
|---|---|
| Plugins give errors or empty output | Wrong profile. Lab 3 is **x86**, so use the first `imageinfo` suggestion |
| `base64: invalid input` | Use `base64 -d` on the file directly, not on copied text. Or add `=` padding |
| XOR output is garbage | Wrong key, or wrong order. Base64-decode **first**, then XOR |
| `steghide: command not found` | `sudo apt install -y steghide` |
| steghide "could not extract" | Passphrase must be the first half **exactly**, including `inctf{` |
| `cp: cannot stat 'dump/script/*.dat'` | The dump was empty. Try another offset |

---
---

# LAB 4 – "Obsession": Step-by-Step Instructions

> **Worth 2 marks. ONE flag.** Format: **`inctf{...}`**
>
> This lab tests one idea: **a file can be deleted, and `dumpfiles` can't get it back, but its content can still be recovered from the NTFS Master File Table (MFT) in memory.**
>
> The path you'll follow:
> 1. List the Desktop files and find a suspicious **image** and an important **text file**.
> 2. Check the image with steganography tools. It's a **deliberate distraction (dead end)**, which you document.
> 3. Try `dumpfiles` on the text file. It **fails**, so you explain why.
> 4. Use **`mftparser`** to recover the text file's content directly from the MFT record and get the flag.
>
> ⚠️ **Placeholders:** most commands set variables automatically. Anything in `CAPITALS_LIKE_THIS` needs your real value. Never type `< >`.

Screenshot names use the pattern `L4-xx_<what>.png`, saved in `~/memlabs/Lab4/screenshots/`.

---

## L4-0. Get the files and set up

### L4-0.1 Download
1. Open https://github.com/stuxnet999/MemLabs, then go to **Lab 4**. Read the description and **📸 SCREENSHOT L4-00_lab4_description**.
2. Download the archive, then:
```bash
mkdir -p ~/memlabs/Lab4/{dump,screenshots,notes}
mv ~/Downloads/MemLabs-Lab4.7z ~/memlabs/Lab4/      # use the real downloaded file name
cd ~/memlabs/Lab4
7z x MemLabs-Lab4.7z
ls -lh
```
**Expected outcome:** `MemoryDump_Lab4.raw` is listed.

### L4-0.2 Steganography tools (for the dead-end check)
```bash
sudo apt install -y steghide libimage-exiftool-perl binwalk
```

### L4-0.3 Start recording and set variables
```bash
cd ~/memlabs/Lab4
script -a ~/memlabs/Lab4/notes/lab4_session.log
PROMPT='[%n@02230297 %1~]$ '
IMG=MemoryDump_Lab4.raw
date; whoami
```

### L4-0.4 Hash the evidence
```bash
md5sum $IMG
sha256sum $IMG
```
**📸 SCREENSHOT L4-01_evidence_hash**

---

## L4-1. Scope the image

### L4-1.1 Profile
```bash
vol -f $IMG imageinfo
```
**Expected outcome:** the first suggestion is **`Win7SP1x64`** (back to 64-bit). Set it, and use whatever is listed **first** if yours differs:
```bash
P=Win7SP1x64
```
**📸 SCREENSHOT L4-02_imageinfo**

### L4-1.2 Processes
```bash
vol -f $IMG --profile=$P pslist | tee notes/pslist.txt
vol -f $IMG --profile=$P pstree | tee notes/pstree.txt
```
**📸 SCREENSHOT L4-03_pslist**

**Expected outcome:** the guidance notes that nothing stands out much here. Note the user-launched applications for your log (look at what runs under `explorer.exe` in `pstree`) and move on to the files.

**(Part B checklist, for the log)** Quick checks. Record what they show, even if it's nothing:
```bash
vol -f $IMG --profile=$P cmdscan
vol -f $IMG --profile=$P consoles
```

---

## L4-2. List the Desktop files (Guidance Q1)

### L4-2.1 filescan
```bash
vol -f $IMG --profile=$P filescan > notes/filescan.txt
grep -i "\\\\Desktop\\\\" notes/filescan.txt
```
**Expected outcome:** files on a user's Desktop. Look for:
- an **image file** (`.jpeg`, `.jpg` or `.png`) with an **odd, suspicious name**
- a **text file** whose name suggests it's **important**

Write down the user name and both file names. **📸 SCREENSHOT L4-04_desktop_files.** Highlight both files.

Put the names in variables. Type the **real names** from your output:
```bash
STEGIMG=SUSPICIOUS_IMAGE_NAME.jpeg
TXTFILE=IMPORTANT_TEXT_NAME.txt
grep -i "$STEGIMG" notes/filescan.txt
grep -i "$TXTFILE" notes/filescan.txt
```

---

## L4-3. The steganography dead end (Guidance Q1)

The guidance says to **expect the image to be a distraction**, but you still have to check it properly and **document it**.

### L4-3.1 Dump the image
```bash
mkdir -p dump/image
OFF=$(grep -i "$STEGIMG" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/image/
ls -la dump/image/
cp dump/image/*.dat dump/$STEGIMG
file dump/$STEGIMG
xdg-open dump/$STEGIMG
```
**📸 SCREENSHOT L4-05_stego_image_dumped** (the image opened, plus the `file` output)

Look at the picture itself. Does it show anything readable? Write down what you see. If it *looks* like a flag, be suspicious: it may be a fake or a taunt.

### L4-3.2 Run basic stego and metadata checks
```bash
exiftool dump/$STEGIMG                                  # metadata: comments, author, software
strings -n 6 dump/$STEGIMG | grep -iE "inctf|flag|pass"  # readable text hidden in the file
binwalk dump/$STEGIMG                                   # other files appended inside the image?
steghide info dump/$STEGIMG                             # press Enter for an empty passphrase
steghide extract -sf dump/$STEGIMG -p "" -xf dump/stego_out.txt
```
**Expected outcome:**
- `exiftool`: normal metadata, no flag
- `strings | grep`: nothing useful
- `binwalk`: only the image itself, no hidden extra files
- `steghide`: `could not extract any data` (or nothing useful)

**📸 SCREENSHOT L4-06_stego_dead_end** (the outputs of these checks)

**For your log:** *"The image was checked with exiftool, strings, binwalk and steghide. No hidden data was found, so it was treated as a deliberate distraction and I moved on to the text file."*

**Why a dead end still counts (put this in your report in your own words):** a forensic investigation must be **complete and repeatable**. Writing down what you checked, and that it found nothing, shows the image was **ruled out**, not ignored. If someone later asks "did you check the image?", your log answers it. It also stops another examiner from repeating the same work.

---

## L4-4. Try dumpfiles on the text file – it fails (Guidance Q2)

### L4-4.1 Attempt the normal extraction
```bash
mkdir -p dump/txt
OFF=$(grep -i "$TXTFILE" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/txt/
ls -la dump/txt/
```
**Expected outcome:**
- `dumpfiles` prints **no `DataSectionObject` or `SharedCacheMap` line** (compare with Labs 1–3, where it always printed one).
- `dump/txt/` is **empty**.

If filescan listed the file more than once, try every offset and log each one:
```bash
for OFF in $(grep -i "$TXTFILE" notes/filescan.txt | awk '{print $1}'); do echo "== $OFF"; vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/txt/; done
ls -la dump/txt/
```
**📸 SCREENSHOT L4-07_dumpfiles_failed** (the command, the empty result, and the empty `ls`)

### L4-4.2 Understand why (for the report)
- `filescan` finds **`_FILE_OBJECT` structures**. These are Windows' "handles" that record that a file *was* opened. They can stay in memory after the file is closed or **deleted**.
- `dumpfiles` doesn't read the disk. It copies the file's **cached data pages** in RAM, found through the file object's **section object pointers** (`DataSectionObject`, `SharedCacheMap`, `ImageSectionObject`).
- When the file was **deleted**, its cached data was released, so those pointers are **empty**. There's a file name in memory, but **no content attached to it**, and `dumpfiles` has nothing to copy.
- **Forensic meaning:** *appearing in a file listing* only proves the file **existed and was accessed**. It doesn't mean its content is still recoverable through that object. You have to look for the content somewhere else.

---

## 🚩 L4-5. Recover the file from the MFT (Guidance Q3)

### L4-5.1 What the MFT is (short version for your report)
- On NTFS, every file has a **1 KB record** in the **Master File Table (`$MFT`)**. The record holds the file's name, timestamps and **`$DATA` attribute**.
- If a file is **small** (roughly under ~700 bytes), NTFS stores its content **inside the MFT record itself**. This is called **resident data**.
- Windows caches MFT records in RAM. When a file is deleted, its MFT record is only **marked as unused**; the bytes, **including resident content**, stay there until they're overwritten.
- **`mftparser`** scans memory for MFT records (they start with the signature `FILE`) and prints each one, including resident `$DATA` content.

### L4-5.2 Run mftparser
This takes a while (**5–15 minutes**) and creates a large file. Let it finish:
```bash
time vol -f $IMG --profile=$P mftparser > notes/mftparser.txt
ls -lh notes/mftparser.txt
wc -l notes/mftparser.txt
```
**Expected outcome:** a text file of several MB with many thousands of lines. **📸 SCREENSHOT L4-08_mftparser_run**

### L4-5.3 Find the missing file's record
```bash
grep -n -i "$TXTFILE" notes/mftparser.txt
```
**Expected outcome:** one or more lines with the file name, with line numbers at the start.

Show the **full record** around it. `$DATA` comes after the name and timestamps:
```bash
grep -i -A 40 "$TXTFILE" notes/mftparser.txt | less
```
(Use the arrow keys to scroll, `q` to quit.)

Look for a section like:
```
$DATA
0000000000: 69 0d 0a 6e 0d 0a ...   i..n..
```
- The **left** part is the **hex bytes**.
- The **right** column is the same bytes as **text**: printable characters are shown, and others (like line breaks `0d 0a`) appear as `.`.
- Reading the right column **top to bottom, ignoring the dots**, gives you the file's content, and that's the **flag**.

If there are several records for the same name, check each one. The one with **hex lines under `$DATA`** is the one you want.

**📸 SCREENSHOT L4-09_mft_record_FLAG.** The assignment specifically requires the MFT-based recovery screenshot. Make sure the **file name**, the **`$DATA`** heading and the **hex/text lines** are all visible.

### L4-5.4 (Recommended) Rebuild the text cleanly from the hex
The flag in the right-hand column is broken up by dots, so this converts the hex bytes back to text to read it exactly.

First, print just the `$DATA` hex lines for the file:
```bash
grep -i -A 40 "$TXTFILE" notes/mftparser.txt | sed -n '/\$DATA/,/^\*\*\*/p' | grep -E "^[0-9a-f]{10}:"
```
Then convert them to text, removing line breaks:
```bash
grep -i -A 40 "$TXTFILE" notes/mftparser.txt | sed -n '/\$DATA/,/^\*\*\*/p' | grep -E "^[0-9a-f]{10}:" \
 | awk '{for(i=2;i<=17;i++) if($i ~ /^[0-9a-f][0-9a-f]$/) printf "%s", $i}' | xxd -r -p | tr -d '\r\n\0' ; echo
```
**Expected outcome:** the clean flag `inctf{...}`. **📸 SCREENSHOT L4-10_FLAG_clean**

> If this prints nothing or garbage, read the flag manually from the right-hand column in L4-5.3 and check it against the hex. In ASCII, `69`=i, `6e`=n, `63`=c, `74`=t, `66`=f, `7b`={, `7d`=}, `5f`=_.

### L4-5.5 (Optional) Extra evidence for the report
Look at the timestamps in the same MFT record:
```bash
grep -i -B 5 -A 15 "$TXTFILE" notes/mftparser.txt | head -40
```
The `$STANDARD_INFORMATION` and `$FILE_NAME` sections show **Creation / Modified / MFT Altered / Access** times. Mentioning when the file was created and last changed strengthens your timeline.

### L4-5.6 Stop recording
```bash
exit
```

---

## L4 Screenshot checklist

| # | Filename | Shows |
|---|----------|-------|
| 00 | `L4-00_lab4_description.png` | Lab README |
| 01 | `L4-01_evidence_hash.png` | md5/sha256 |
| 02 | `L4-02_imageinfo.png` | Profile |
| 03 | `L4-03_pslist.png` | Processes |
| 04 | `L4-04_desktop_files.png` | Desktop files: image + text file |
| 05 | `L4-05_stego_image_dumped.png` | Image extracted/opened |
| 06 | `L4-06_stego_dead_end.png` | exiftool/strings/binwalk/steghide: nothing found |
| 07 | `L4-07_dumpfiles_failed.png` | **dumpfiles on the text file = nothing** |
| 08 | `L4-08_mftparser_run.png` | mftparser ran, output size |
| 09 | `L4-09_mft_record_FLAG.png` | **MFT record with resident $DATA = flag** |
| 10 | `L4-10_FLAG_clean.png` | Flag rebuilt cleanly from hex |

---

## L4 What to write in the report

1. **The flag**, with screenshot L4-09 (MFT-based recovery, which is required).
2. **Required paragraph – why `dumpfiles` failed but `mftparser` worked.** In your own words, cover:
   - `filescan` found the file's **`_FILE_OBJECT`**, which proves the file existed and was opened,
   - `dumpfiles` needs the **cached data pages** linked from that object; the file was **deleted**, so those were gone and the pointers were empty, leaving nothing to dump,
   - NTFS stores **small files' content inside the MFT record** (resident `$DATA`),
   - deleting a file only **marks the MFT record as free**; the record (with its content) stayed in RAM,
   - `mftparser` reads MFT records **directly** by their `FILE` signature, so it found the content even though the file object had no data.
3. **Investigation log**, including:
   - the **stego dead end**: what you ran (exiftool, strings, binwalk, steghide) and what each showed,
   - **why you moved on** (no hidden data, the guidance called it a distraction, and the text file was the more promising lead),
   - **why a dead end is still valuable** (it rules things out, makes the work complete and repeatable, and stops someone redoing it),
   - every `dumpfiles` attempt that returned nothing.
4. **Forensic reasoning:** "existing in a listing" ≠ "recoverable content"; different artifacts (file objects vs MFT records) survive deletion differently.

## L4 Common problems

| Problem | Fix |
|---|---|
| `mftparser` seems stuck | It's slow. Wait 5–15 min. Check the file is growing with `ls -lh notes/mftparser.txt` in another terminal |
| `grep` finds the name but no `$DATA` hex below it | Try `-A 60`, or look at the other matching records. Only one has resident data |
| The hex→text command prints nothing | Read the flag manually from the right-hand text column; check it against the hex values |
| `dumpfiles` on the image is also empty | Try another offset (`sed -n 2p` instead of `head -1`). Log it |
| Desktop grep shows nothing | Use `grep -i desktop notes/filescan.txt` (simpler pattern) |

---
---

# LAB 5 – "Black Tuesday": Step-by-Step Instructions

> **Worth 2 marks. TWO flags.** The first flag is the **password** for the archive that holds the second.
>
> The path you'll follow:
> 1. Find the **archive manager** process and the **archive** it had open, then extract it from memory. It asks for a password. **Don't brute-force it.**
> 2. Read the **Internet Explorer / Windows Explorer history** with the **built-in** `iehistory` plugin (not the community `chromehistory` from Lab 2).
> 3. Find an **unusually long, encoded-looking file name** in that history, then **decode it**. That's **Flag 1**.
> 4. Use Flag 1 as the archive password, open the archive, and get **Flag 2**.
>
> ⚠️ **Placeholders:** most commands set variables automatically. Anything in `CAPITALS_LIKE_THIS` needs your real value. Never type `< >`.
> ⚠️ **Special characters:** flags in this lab can contain `!` and `$`. **Always use single quotes** `'...'` around them, or store them in a variable, so zsh doesn't change them.

Screenshot names use the pattern `L5-xx_<what>.png`, saved in `~/memlabs/Lab5/screenshots/`.

---

## L5-0. Get the files and set up

### L5-0.1 Download
1. Open https://github.com/stuxnet999/MemLabs, then go to **Lab 5**. Read the description and **📸 SCREENSHOT L5-00_lab5_description**.
2. Download the archive, then:
```bash
mkdir -p ~/memlabs/Lab5/{dump,screenshots,notes}
mv ~/Downloads/MemLabs-Lab5.7z ~/memlabs/Lab5/      # use the real downloaded file name
cd ~/memlabs/Lab5
7z x MemLabs-Lab5.7z
ls -lh
```
**Expected outcome:** `MemoryDump_Lab5.raw` is listed.

### L5-0.2 Tools
```bash
sudo apt install -y unrar p7zip-full
```

### L5-0.3 Start recording and set variables
```bash
cd ~/memlabs/Lab5
script -a ~/memlabs/Lab5/notes/lab5_session.log
PROMPT='[%n@02230297 %1~]$ '
IMG=MemoryDump_Lab5.raw
unset VOLATILITY_KDBG
date; whoami
```

### L5-0.4 Hash the evidence
```bash
md5sum $IMG
sha256sum $IMG
```
**📸 SCREENSHOT L5-01_evidence_hash**

---

## L5-1. Scope the image

### L5-1.1 Profile
```bash
vol -f $IMG imageinfo
```
**Expected outcome:** the first suggestion is **`Win7SP1x64`**. Use whatever is listed **first**:
```bash
P=Win7SP1x64
```
**📸 SCREENSHOT L5-02_imageinfo**

### L5-1.2 Processes (Guidance Q1)
```bash
vol -f $IMG --profile=$P pslist | tee notes/pslist.txt
vol -f $IMG --profile=$P pstree | tee notes/pstree.txt
```
**Expected outcome:** a normal process list. Look for:
- an **archive manager**: **`WinRAR.exe`**
- a **web browser**: is it Chrome, Firefox or **Internet Explorer** (`iexplore.exe`)? Note which.
- any other user programs (e.g. Notepad), and **`DumpIt.exe`** (the capture tool again)

```bash
grep -iE "winrar|iexplore|chrome|firefox|notepad|dumpit" notes/pslist.txt
```
**📸 SCREENSHOT L5-03a_pslist**, **📸 L5-03b_key_processes**

> **If `pslist` fails with `Could not list tasks`** (the same problem as Lab 4):
> 1. Log it and **📸 L5-03x_pslist_error**.
> 2. Run `vol -f $IMG --profile=$P kdbgscan | tee notes/kdbgscan.txt` and `grep -E "Offset \(V\)|PsActiveProcessHead" notes/kdbgscan.txt`.
> 3. If one block shows **`(N processes)` with N > 0**, run `export VOLATILITY_KDBG=<that Offset (V) value>` (type the hex value itself, not the `< >`), then retry `pslist`.
> 4. Otherwise use **`psscan`**: `vol -f $IMG --profile=$P psscan | tee notes/pslist.txt`.

Save the WinRAR PID automatically:
```bash
RAR_PID=$(grep -i winrar notes/pslist.txt | head -1 | awk '{print $3}'); echo "WinRAR PID = $RAR_PID"
```
(With `psscan` output the PID is also the 3rd column, so this works for both.)

---

## L5-2. The archive (Guidance Q1)

### L5-2.1 Which archive did WinRAR open?
```bash
vol -f $IMG --profile=$P cmdline -p $RAR_PID
```
**Expected outcome:** `Command line : "C:\Program Files\WinRAR\WinRAR.exe" "C:\Users\...\SOMETHING.rar"`. The **archive name itself looks odd**: it isn't a normal word, it looks **encoded**.

**📸 SCREENSHOT L5-04_cmdline_winrar**

> If `cmdline -p` gives nothing because `pslist` was broken, use the physical offset from `psscan` (1st column): `vol -f $IMG --profile=$P cmdline --offset=0x...`. Or skip ahead and find the `.rar` in `filescan` (next step).

Save the archive name. Type the real name you saw, e.g. `RARNAME=Abc123.rar`:
```bash
RARNAME=ARCHIVE_NAME.rar
echo $RARNAME
```

**(For your log)** The archive name looks like Base64. Try decoding the part before `.rar`, and write down what it means:
```bash
echo "${RARNAME%.rar}" | base64 -d ; echo
```

### L5-2.2 Find the archive in memory and extract it
```bash
vol -f $IMG --profile=$P filescan > notes/filescan.txt
grep -i "\.rar" notes/filescan.txt
```
**📸 SCREENSHOT L5-05_filescan_rar**

```bash
mkdir -p dump/rar
OFF=$(grep -i "$RARNAME" notes/filescan.txt | head -1 | awk '{print $1}'); echo $OFF
vol -f $IMG --profile=$P dumpfiles -Q $OFF -D dump/rar/
ls -la dump/rar/
cp dump/rar/*.dat dump/$RARNAME
file dump/$RARNAME
```
**Expected outcome:** `file` says **RAR archive data**. **📸 SCREENSHOT L5-06_dumpfiles_rar**

> If `dump/rar/` is empty, try the next offset (`sed -n 2p` instead of `head -1`). Log it.

### L5-2.3 Try to open it – password needed
```bash
unrar l dump/$RARNAME
unrar x dump/$RARNAME dump/
```
**Expected outcome:** it lists the file inside (an image) and **asks for a password**. Press `Ctrl+C` to cancel.

**📸 SCREENSHOT L5-07_rar_password_prompt**

**Don't brute-force it.** The guidance says the password is somewhere in the evidence. **For your log:** *"The archive was password-protected. Rather than guessing or brute-forcing, which is slow, unreliable and doesn't explain anything forensically, I looked for the password elsewhere in memory."*

**(Part B checklist, for the log)** Quick checks before moving to the browser. Note the result even if it's "nothing relevant":
```bash
vol -f $IMG --profile=$P cmdscan
vol -f $IMG --profile=$P consoles
vol -f $IMG --profile=$P envars | grep -iE "flag|pass|key"
```

---

## 🚩 L5-3. FLAG 1 – Browser history (Guidance Q2 & Q3)

### L5-3.1 Which history plugin, and why
- Lab 2 used **Chrome**, which stores history in an **SQLite database**, so you needed the community **`chromehistory`** plugin.
- This system uses **Internet Explorer**. IE (and Windows Explorer) record history in **`index.dat`** files through the **WinINet** library.
- Volatility 2 has a **built-in** plugin for that: **`iehistory`**. It scans process memory for index.dat records (`URL `, `LEAK`, `REDR`). It also catches **local file access** (`file:///` entries), because Windows Explorer uses the same WinINet history.

### L5-3.2 Run iehistory
```bash
vol -f $IMG --profile=$P iehistory > notes/iehistory.txt
wc -l notes/iehistory.txt
grep -i "Location" notes/iehistory.txt | sort -u | head -60
```
**Expected outcome:** many entries like `Location: Visited: SmartNet@file:///C:/Users/...` or `...@http://...`, attached to processes such as `explorer.exe` and `iexplore.exe`.

**📸 SCREENSHOT L5-08_iehistory**

### L5-3.3 Find the unusually long, encoded-looking file name
Normal file names are words, like `report.docx` or `photo.jpg`. Look for a **very long random-looking name** (letters and digits, possibly starting with `Zmxh`, which is Base64 for `fla`):
```bash
grep -oE "[A-Za-z0-9+/=_-]{25,}\.[A-Za-z0-9]{2,4}" notes/iehistory.txt | sort -u
```
**Expected outcome:** one (maybe a few) long file names. The odd one is **much longer than anything else** and looks encoded. Show the full entry for it:
```bash
grep -i "PASTE_THE_LONG_NAME" notes/iehistory.txt | head -5
```
**📸 SCREENSHOT L5-09_encoded_filename.** Highlight the long name.

### L5-3.4 Decode it
Put **only the name part** (without the extension, e.g. without `.bmp`) in a variable:
```bash
ENC='PASTE_LONG_NAME_WITHOUT_EXTENSION'
echo "$ENC" | base64 -d ; echo
```
If you get **`base64: invalid input`**, the `=` padding was removed from the file name. Base64 length must be a multiple of 4, so add the padding automatically:
```bash
B="$ENC"; while [ $(( ${#B} % 4 )) -ne 0 ]; do B="$B="; done; echo "$B"
echo "$B" | base64 -d ; echo
```
**Expected outcome:** a readable **`flag{...}`**. This is **Lab 5 Flag 1**.

**📸 SCREENSHOT L5-10_FLAG1_decoded**

Save it **exactly**, using the variable so you don't have to retype special characters:
```bash
FLAG1=$(echo "$B" | base64 -d)
echo "$FLAG1"
```
(If the first decode worked without padding, use `FLAG1=$(echo "$ENC" | base64 -d)` instead.)

---

## 🚩 L5-4. FLAG 2 – Open the archive (Guidance Q4)

### L5-4.1 Extract with Flag 1 as the password
```bash
unrar x -p"$FLAG1" dump/$RARNAME dump/
```
If `unrar` complains, use 7z:
```bash
7z x -p"$FLAG1" dump/$RARNAME -odump/
```
**Expected outcome:** `All OK` / `Everything is Ok`, and an image file is extracted.

**📸 SCREENSHOT L5-11_rar_extracted**

> **If the password is wrong:**
> - Run `echo "$FLAG1"` and check it's the **full** flag, including `flag{` and `}`.
> - Make sure there's no trailing newline or space (the variable method avoids this).
> - Delete any 0-byte file left by the failed attempt (`ls -la dump/`, then `rm dump/EMPTY_FILE`). In Lab 2, a failed attempt left a 0-byte file behind.
> - Log every attempt.

### L5-4.2 View the image
```bash
ls -la dump/
xdg-open dump/EXTRACTED_IMAGE.png      # use the real name from ls
```
**Expected outcome:** an image showing **`flag{...}`**. This is **Lab 5 Flag 2**.

**📸 SCREENSHOT L5-12_FLAG2_image**

### L5-4.3 Stop recording
```bash
exit
```

---

## L5 Screenshot checklist

| # | Filename | Shows |
|---|----------|-------|
| 00 | `L5-00_lab5_description.png` | Lab README |
| 01 | `L5-01_evidence_hash.png` | md5/sha256 |
| 02 | `L5-02_imageinfo.png` | Profile |
| 03a/b | `L5-03a_pslist.png`, `L5-03b_key_processes.png` | WinRAR, browser, etc. |
| 04 | `L5-04_cmdline_winrar.png` | Archive path |
| 05 | `L5-05_filescan_rar.png` | Archive in filescan |
| 06 | `L5-06_dumpfiles_rar.png` | Archive extracted from memory |
| 07 | `L5-07_rar_password_prompt.png` | Password needed |
| 08 | `L5-08_iehistory.png` | iehistory output |
| 09 | `L5-09_encoded_filename.png` | Long encoded file name |
| 10 | `L5-10_FLAG1_decoded.png` | **Flag 1** |
| 11 | `L5-11_rar_extracted.png` | Archive opened with Flag 1 |
| 12 | `L5-12_FLAG2_image.png` | **Flag 2** |

---

## L5 What to write in the report

1. **Both flags** with screenshots L5-10 and L5-12.
2. **Required sentence – the browser plugin.** For example, in your own words: *"I used Volatility's built-in `iehistory` plugin because this system used Internet Explorer, which stores history in WinINet `index.dat` records that `iehistory` parses from memory, whereas the community `chromehistory` plugin from Lab 2 only reads Chrome's SQLite `History` database."*
3. **Investigation log:**
   - the process list and why WinRAR was the lead,
   - the `cmdline` → `filescan` → `dumpfiles` path to the archive,
   - the password prompt and **why you didn't brute-force** (the password was in the evidence; brute-forcing is slow and proves nothing),
   - the cmdscan/consoles/envars checks (dead ends),
   - the iehistory search, the long file name, and any padding problem with Base64,
   - any failed password attempts.
4. **Forensic reasoning:**
   - `iehistory` showed a **local file** (`file:///`), not just websites, because Windows Explorer records file access in the same WinINet history. So browser history can reveal files a user opened, even if the files are gone.
   - Base64 in a file name hides meaning from a quick look, and decoding it turned it into evidence.
   - The chain: **history artifact → decoded name → archive password → second flag** shows how separate artifacts in memory connect.

## L5 Common problems

| Problem | Fix |
|---|---|
| `pslist`: Could not list tasks | Same as Lab 4: use `kdbgscan` + `VOLATILITY_KDBG`, or `psscan` |
| `cmdline -p` shows nothing | Use `--offset=` from psscan, or go straight to `filescan \| grep -i .rar` |
| `iehistory` output is huge | It's saved to `notes/iehistory.txt`. Use the `grep -oE` command to find long names |
| `base64: invalid input` | Add `=` padding (L5-3.4), and remove the file extension first |
| RAR password wrong | Use `-p"$FLAG1"` (the variable), check the full `flag{...}`, and remove 0-byte leftovers |
| `zsh: event not found` | You typed a flag with `!` inside double quotes. Use single quotes or the `$FLAG1` variable |
