import os
import sys
import time
import re
import json
import random
import string
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

try:
    from faker import Faker
except ImportError:
    os.system("pip install faker requests colorama")
    from faker import Faker

init(autoreset=True)

class Config:
    BASE_PATH = "/sdcard/boostphere"
    FILES = {
        "1": "FRAACCOUNT.txt",
        "2": "FRAPAGES.txt",
        "3": "RPWACCOUNT.txt",
        "4": "RPWPAGES.txt"
    }
    # These domains are used in the original script to bypass WAF
    REG_DOMAINS = [
        "https://x.facebook.com/reg/",
        "https://mbasic.facebook.com/reg/",
        "https://m.facebook.com/reg/"
    ]
    # Signature used for the 'Handshake'
    API_KEY = '62f8ce9f74b12f84c123cc23437a4a32'
    ACCESS_TOKEN_SEED = '350685531728|62f8ce9f74b12f84c123cc23437a4a32'

class UI:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL
    LINE = f"{CYAN}────────────────────────────────────────────────────────{RESET}"

    @staticmethod
    def banner():
        os.system("cls" if os.name == "nt" else "clear")
        print(UI.LINE)
        print(f"{UI.YELLOW}             FB-BOOST ULTIMATE {UI.WHITE}v3.0{UI.RESET}")
        print(f"{UI.WHITE}        Functional Scrape Replication (Termux){UI.RESET}")
        print(UI.LINE)

    @staticmethod
    def log(prefix, message, color=WHITE):
        time_now = time.strftime("%H:%M:%S")
        print(f"[{time_now}] {color}[{prefix}] {UI.RESET}{message}")

class TempMail:
    @staticmethod
    def get_email():
        domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = random.choice(domains)
        return f"{user}@{domain}", user, domain

    @staticmethod
    def get_otp(user, domain):
        api = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
        for _ in range(12):
            try:
                r = requests.get(api, timeout=5).json()
                if r:
                    msg_id = r[0]['id']
                    msg_url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain={domain}&id={msg_id}"
                    msg_data = requests.get(msg_url).json()
                    code = re.search(r'\b\d{5}\b', msg_data.get('body', ''))
                    if code: return code.group(0)
            except: pass
            time.sleep(5)
        return None

class FacebookAutomation:
    def __init__(self):
        self.session = requests.Session()
        self.faker = Faker()
        self.ua = self.generate_ua()

    def generate_ua(self):
        android_v = random.randint(9, 13)
        fb_v = f"{random.randint(200, 440)}.0.0.{random.randint(10, 99)}.{random.randint(100, 200)}"
        return f"Dalvik/2.1.0 (Linux; U; Android {android_v}; SM-G960F Build/R16NW) [FBAN/Orca-Android;FBAV/{fb_v};FBPN/com.facebook.orca;FBLC/en_US;FBBV/{random.randint(100000000, 999999999)};FBCR/Carrier;FBMF/samsung;FBBD/samsung;FBDV/SM-G960F;FBSV/{android_v}.0.0;]"

    def get_handshake_tokens(self):
        for url in Config.REG_DOMAINS:
            try:
                self.session.headers.update({'User-Agent': self.ua})
                resp = self.session.get(url, timeout=10)
                html = resp.text
                return {
                    'lsd': re.search(r'name="lsd" value="(.*?)"', html).group(1),
                    'jazoest': re.search(r'name="jazoest" value="(.*?)"', html).group(1),
                    'm_ts': re.search(r'name="m_ts" value="(.*?)"', html).group(1),
                    'li': re.search(r'name="li" value="(.*?)"', html).group(1),
                    'reg_instance': re.search(r'name="reg_instance" value="(.*?)"', html).group(1),
                    'reg_impression_id': re.search(r'name="reg_impression_id" value="(.*?)"', html).group(1)
                }
            except: continue
        return None

    def register(self):
        tokens = self.get_handshake_tokens()
        if not tokens:
            UI.log("FAIL", "Bypass failed. Reset Airplane Mode.", UI.RED)
            return

        email, user, domain = TempMail.get_email()
        fname, lname = self.faker.first_name(), self.faker.last_name()
        pwd = f"Nova@{random.randint(100,999)}!"
        # Browser Password Encryption (mimics original script)
        encpass = f"#PWD_BROWSER:0:{int(time.time())}:{pwd}"

        payload = {
            **tokens,
            'ccp': '2', 'ns': '1', 'app_id': '103', 'submission_request': 'true',
            'firstname': fname, 'lastname': lname, 'reg_email__': email,
            'sex': random.choice(['1', '2']), 'reg_passwd__': pwd, 'encpass': encpass,
            'birthday_day': str(random.randint(1, 28)),
            'birthday_month': str(random.randint(1, 12)),
            'birthday_year': str(random.randint(1995, 2006)),
            'submit': 'Sign Up'
        }

        try:
            resp = self.session.post("https://x.facebook.com/reg/submit/", data=payload, timeout=15)
            if "confirmemail" in resp.url or "checkpoint" in resp.url:
                UI.log("WAIT", f"Verification sent to {email}", UI.YELLOW)
                otp = TempMail.get_otp(user, domain)
                if otp:
                    self.verify_otp(otp, email, pwd)
                else:
                    UI.log("FAIL", "OTP Timeout (Email domain flagged)", UI.RED)
            elif "c_user" in self.session.cookies.get_dict():
                self.save_account(email, pwd, self.session.cookies.get_dict())
                UI.log("SUCCESS", f"Live: {fname}", UI.GREEN)
            else:
                UI.log("FAIL", "Meta blocked the request", UI.RED)
        except Exception as e:
            UI.log("ERROR", "Connection Timeout", UI.RED)

    def verify_otp(self, otp, email, pwd):
        data = {'c': otp, 'submit': 'Confirm'}
        try:
            r = self.session.post("https://m.facebook.com/confirmemail.php", data=data, timeout=10)
            if "c_user" in self.session.cookies.get_dict():
                self.save_account(email, pwd, self.session.cookies.get_dict())
                UI.log("SUCCESS", "Account Verified!", UI.GREEN)
            else:
                UI.log("FAIL", "Checkpoint after OTP", UI.RED)
        except: pass

    def save_account(self, email, pwd, cookies):
        c_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        with open(os.path.join(Config.BASE_PATH, "FRAACCOUNT.txt"), "a") as f:
            f.write(f"{email}|{pwd}|{c_str}\n")

    def perform_boost(self, token, target_id, action, data=None):
        headers = {'User-Agent': self.ua}
        base_url = f"https://graph.facebook.com/{target_id}"
        params = {'access_token': token}

        try:
            if action == "REACT":
                r = requests.post(f"{base_url}/reactions", params={**params, 'type': data.upper()}, headers=headers)
            elif action == "COMMENT":
                r = requests.post(f"{base_url}/comments", params={**params, 'message': data}, headers=headers)
            elif action == "SHARE":
                r = requests.post(f"https://graph.facebook.com/me/feed", params={**params, 'link': f"fb.com/{target_id}", 'published': '0'}, headers=headers)
            elif action == "FOLLOW":
                r = requests.post(f"{base_url}/subscribers", params=params, headers=headers)
            return r.status_code == 200
        except: return False

# --- UTILS & MENUS ---
def ensure():
    if not os.path.exists(Config.BASE_PATH): os.makedirs(Config.BASE_PATH)
    for f in Config.FILES.values():
        path = os.path.join(Config.BASE_PATH, f)
        if not os.path.exists(path): open(path, 'a').close()

def menu_reg():
    UI.banner()
    amt = int(input(f"{UI.CYAN}Number of accounts to create > {UI.RESET}"))
    bot = FacebookAutomation()
    for i in range(amt):
        print(f"\n{UI.WHITE}--- Account {i+1}/{amt} ---")
        bot.register()
        if i < amt - 1:
            UI.log("INFO", "Resetting IP (Toggle Airplane Mode)...", UI.CYAN)
            time.sleep(10)
    input(f"\n{UI.WHITE}Press Enter to Back...")

def menu_boost():
    UI.banner()
    bot = FacebookAutomation()
    for k, v in Config.FILES.items(): print(f"[{k}] {v}")
    choice = input(f"{UI.CYAN}Select Source > {UI.RESET}")
    
    path = os.path.join(Config.BASE_PATH, Config.FILES.get(choice, "FRAACCOUNT.txt"))
    with open(path, 'r') as f:
        tokens = []
        for line in f:
            match = re.search(r'EAA\w+', line)
            if match: tokens.append(match.group(0))
    
    if not tokens:
        print(f"{UI.RED}No tokens found! Extract or Register first.")
        time.sleep(2)
        return

    print(f"\n{UI.YELLOW}[1] React [2] Comment [3] Share [4] Follow")
    act_type = input(f"{UI.CYAN}Action > {UI.RESET}")
    target = input(f"{UI.WHITE}Target ID/URL > {UI.RESET}")
    # Extract ID
    if "/" in target: 
        if "fbid=" in target: target = target.split("fbid=")[1].split("&")[0]
        else: target = target.split("/")[-1].split("?")[0]

    extra = None
    if act_type == '1': extra = input("Type (LIKE, LOVE, HAHA, etc) > ")
    elif act_type == '2': extra = input("Comment Text > ")
    
    limit = int(input(f"{UI.WHITE}Use how many accounts? (Max {len(tokens)}) > {UI.RESET}"))
    
    UI.log("RUN", "Boosting in progress...", UI.CYAN)
    success = 0
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(bot.perform_boost, tokens[i], target, ["","REACT","COMMENT","SHARE","FOLLOW"][int(act_type)], extra) for i in range(min(limit, len(tokens)))]
        for f in as_completed(futures):
            if f.result(): success += 1
            print(f"\r{UI.GREEN}Progress: {success}", end="")
    print("\n")
    input(f"{UI.WHITE}Finished. Enter to Back...")

def main():
    ensure()
    while True:
        UI.banner()
        print(f"{UI.YELLOW}[1] Multi-Domain Auto Register")
        print(f"{UI.YELLOW}[2] Mass Boosting Tools")
        print(f"{UI.YELLOW}[3] Clean Storage")
        print(f"{UI.YELLOW}[0] Exit")
        print(UI.LINE)
        sel = input(f"{UI.CYAN}Select > {UI.RESET}")
        if sel == '1': menu_reg()
        elif sel == '2': menu_boost()
        elif sel == '3':
            for f in Config.FILES.values(): open(os.path.join(Config.BASE_PATH, f), 'w').close()
            print(f"{UI.GREEN}Wiped.")
            time.sleep(1)
        elif sel == '0': sys.exit()

if __name__ == "__main__":
    main()
