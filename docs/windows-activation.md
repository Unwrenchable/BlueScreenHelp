# Windows Activation Guide

How to find, recover, and apply a legitimate Windows product key — so your copy of Windows is properly activated after a repair or reinstall.

> **Important**: This guide covers only **legitimate** Microsoft licensing methods. Pirated keys, key generators, and unofficial activators violate Microsoft's Terms of Service, expose your PC to malware, and are illegal in many countries. Use only genuine keys.

---

## How Windows Activation Works

Windows uses two types of licenses:

### 1. Digital License (most modern PCs)
- Tied to your motherboard's hardware ID.
- No key to write down — Microsoft's servers remember your license.
- After reinstalling Windows on the **same PC**, activation happens automatically when you connect to the internet.
- Linked to your **Microsoft account** if you chose that during setup — allows moving the license to a new PC in some cases.

### 2. Product Key (25-character key)
- Format: `XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`
- Used for retail boxes, digital purchases, volume licensing, or OEM copies.
- Required if digital license is not present or if you're moving to new hardware.

---

## Step 1 — Check If You're Already Activated

Before doing anything else, check whether Windows is already activated (digital license may kick in automatically after reinstall):

1. **Settings** → **System** → **Activation**.
2. If it says **"Windows is activated"** or **"Windows is activated with a digital license"** — you're done!
3. If it says **"Windows is not activated"** — continue below.

---

## Step 2 — Find Your Existing Product Key

### Method A — Sticker on Your PC

- **Desktops**: Check the side or top of the case.
- **Laptops**: Check the bottom panel.
- **OEM PCs (Dell, HP, Lenovo, etc.)**: The key is often embedded in the UEFI firmware — you don't need the sticker. Windows reads it automatically during installation.

### Method B — Retrieve Key from a Working Windows Installation

If Windows still boots (or if you can access the drive), you can extract the key that's stored in the registry.

**Using PowerShell (run as Administrator):**
```powershell
(Get-WmiObject -query 'select * from SoftwareLicensingService').OA3xOriginalProductKey
```

If this returns nothing, the key is a generic OEM key or your license is fully digital (tied to hardware, no static key to retrieve).

**Using a free key viewer** (for display only — doesn't generate or crack keys):
- **NirSoft ProduKey**: [nirsoft.net/utils/product_cd_key_viewer.html](https://www.nirsoft.net/utils/product_cd_key_viewer.html) — reads the key from a live or dead Windows installation
- **Magical Jelly Bean Keyfinder**: [magicaljellybean.com](https://www.magicaljellybean.com/keyfinder/) — another free, trusted option

> These tools read the key stored in YOUR system's registry. They do not generate keys or access external servers.

### Method C — Microsoft Account Digital License

If you previously linked Windows to your Microsoft account:

1. Go to **[account.microsoft.com/devices](https://account.microsoft.com/devices)** and sign in.
2. Find your device under **Devices**.
3. Select it → **View Windows license** to see details about your digital license.

To transfer to a new PC after a hardware change:
1. On the newly installed Windows: **Settings** → **System** → **Activation** → **Troubleshoot**.
2. Select **"I changed hardware on this device recently"**.
3. Sign in with your Microsoft account → select your device → **Activate**.

---

## Step 3 — Enter Your Product Key

**Settings → System → Activation → Change product key**

Type the 25-character key and click **Next** → **Activate**.

Or from Command Prompt (Admin):
```cmd
slmgr.vbs /ipk XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
slmgr.vbs /ato
```

---

## Step 4 — If Activation Fails

### Online Activation Failed

1. Check your internet connection.
2. Try the **Activation Troubleshooter**: **Settings → System → Activation → Troubleshoot**.
3. If it says the key is already in use on too many devices, contact Microsoft Support (see below).

### Phone Activation (for offline or repeated-use scenarios)

1. Open Command Prompt as Admin → run `slui 4`.
2. Select your country.
3. Call the toll-free number shown.
4. Follow the automated system: read out the Installation ID displayed → receive a Confirmation ID → enter it.

### Contact Microsoft Support

If you have a legitimate key but activation is not working:
- **Microsoft Support Chat**: [support.microsoft.com](https://support.microsoft.com)
- **Phone**: 1-800-642-7676 (US) — Microsoft's genuine software hotline

---

## Purchasing a New License

If you need to buy Windows:

| Where to Buy | Notes |
|---|---|
| **Microsoft Store** | [microsoft.com/store](https://www.microsoft.com/store) — official, instant digital delivery |
| **Microsoft 365** | Includes Microsoft 365 apps + 1 TB OneDrive. Some plans include a Windows license. |
| **Authorized Retailers** | Amazon, Best Buy, Newegg, B&H — look for "sold by Microsoft" or authorized sellers |

**Current Pricing (USD, approximate):**
- Windows 11 Home: ~$139
- Windows 11 Pro: ~$199
- Windows 11 Pro upgrade from Home: ~$99

> **Students and educators**: Check [microsoft.com/education](https://www.microsoft.com/en-us/education) — many schools provide free or discounted Windows licenses through Microsoft Imagine / Azure Dev Tools for Teaching.

---

## Common Activation Error Codes

| Error Code | Meaning | Fix |
|---|---|---|
| 0xC004F213 | Hardware change detected — digital license can't auto-activate | Use Activation Troubleshooter; sign in with Microsoft account |
| 0xC004C003 | Product key blocked or invalid | Contact Microsoft Support |
| 0xC004F025 | Key already used on another PC | Contact Microsoft Support to transfer |
| 0x803F7001 | No product key found | Enter your key manually or link Microsoft account |
| 0xC004E016 | Invalid product key format | Double-check you entered all 25 characters correctly |
| 0x8007007B | DNS or network issue | Check internet; try phone activation |

---

## What Happens Without Activation

Windows 11/10 runs without activation but with limitations:
- Watermark in the bottom-right corner: **"Activate Windows"**
- Personalization settings locked (can't change wallpaper, colors, themes)
- May receive periodic reminders to activate
- All security updates and features still work normally

---

## Frequently Asked Questions

**Q: Can I use my old Windows 7 or 8.1 key to activate Windows 10/11?**  
A: Microsoft's free upgrade offer for Windows 7/8.1 officially ended in 2016, but in practice many of these keys still activate Windows 10/11. Try entering your key in **Settings → Activation → Change product key**. If it doesn't work, you'll need a new license.

**Q: I bought a PC with Windows pre-installed. Do I need a key to reinstall?**  
A: No — modern OEM PCs embed the key in the UEFI firmware. Windows reads it automatically during a clean install and activates online. The key is also retrievable with ProduKey if needed.

**Q: My digital license was for Windows 10 Pro. After reinstalling, I got Home.**  
A: During reinstall setup, make sure to select **Windows 10/11 Pro** when prompted for the edition. Don't enter a key during setup — just click "I don't have a product key" and let the digital license handle it after first boot.

**Q: Can I activate Windows without internet?**  
A: Yes — use **Phone Activation** (run `slui 4` from Command Prompt). Microsoft's automated system gives you a Confirmation ID over the phone.

---

## Links Summary

| Resource | URL |
|---|---|
| Check activation status | Settings → System → Activation |
| Microsoft account devices | [account.microsoft.com/devices](https://account.microsoft.com/devices) |
| Microsoft Support | [support.microsoft.com](https://support.microsoft.com) |
| Buy Windows 11 | [microsoft.com/store](https://www.microsoft.com/store) |
| NirSoft ProduKey | [nirsoft.net/utils/product_cd_key_viewer.html](https://www.nirsoft.net/utils/product_cd_key_viewer.html) |
| Student/Education licensing | [microsoft.com/education](https://www.microsoft.com/en-us/education) |
