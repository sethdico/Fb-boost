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
    REG_URL = "https://x.facebook.com/reg/"
    SUBMIT_URL = "https://x.facebook.com/reg/submit/"
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
        print(f"{UI.YELLOW}             NOVA BOOSTING SUITE {UI.WHITE}v2.0{UI.RESET}")
        print(f"{UI.WHITE}        Multi-Threaded Automation for Termux{UI.RESET}")
        print(UI.LINE)

    @staticmethod
    def log(prefix, message, color=WHITE):
        time_now = time.strftime("%H:%M:%S")
        print(f"[{time_now}] {color}[{prefix}] {UI.RESET}{message}")

class Utils:
    @staticmethod
    def get_user_agent():
        version = random.randint(110, 125)
        android = random.randint(10, 13)
        model = f"SM-S9{random.randint(0,2)}8B"
        return (f"Mozilla/5.0 (Linux; Android {android}; {model}) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Mobile Safari/537.36")

    @staticmethod
    def ensure_files():
        if not os.path.exists(Config.BASE_PATH):
            try:
                os.makedirs(Config.BASE_PATH)
            except OSError:
                pass
        for file_name in Config.FILES.values():
            full_path = os.path.join(Config.BASE_PATH, file_name)
            if not os.path.exists(full_path):
                open(full_path, 'a').close()

    @staticmethod
    def extract_id(url):
        try:
            if "posts/" in url: return url.split("posts/")[1].split("/")[0].split("?")[0]
            if "videos/" in url: return url.split("videos/")[1].split("/")[0].split("?")[0]
            if "reel/" in url: return url.split("reel/")[1].split("/")[0].split("?")[0]
            if "fbid=" in url: return url.split("fbid=")[1].split("&")[0]
            if "id=" in url: return url.split("id=")[1].split("&")[0]
            if url.isdigit(): return url
            return url 
        except:
            return None

class TempMail:
    @staticmethod
    def generate():
        domains = ["1secmail.com", "1secmail.org", "1secmail.net"]
        login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = random.choice(domains)
        return f"{login}@{domain}", login, domain

    @staticmethod
    def get_code(login, domain):
        api = "https://www.1secmail.com/api/v1/"
        for _ in range(12):
            try:
                r = requests.get(f"{api}?action=getMessages&login={login}&domain={domain}").json()
                if r:
                    msg_id = r[0]['id']
                    r = requests.get(f"{api}?action=readMessage&login={login}&domain={domain}&id={msg_id}").json()
                    body = r.get('textBody', '') + r.get('subject', '')
                    code = re.search(r'\b\d{5}\b', body)
                    if code: return code.group(0)
            except: pass
            time.sleep(5)
        return None

class AccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Utils.get_user_agent(),
            'Accept-Language': 'en-US,en;q=0.9',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-mobile': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        self.faker = Faker()

    def create(self):
        try:
            resp = self.session.get(Config.REG_URL)
            data = resp.text
            payload = {
                'lsd': re.search(r'name="lsd" value="(.*?)"', data).group(1),
                'jazoest': re.search(r'name="jazoest" value="(.*?)"', data).group(1),
                'm_ts': re.search(r'name="m_ts" value="(.*?)"', data).group(1),
                'li': re.search(r'name="li" value="(.*?)"', data).group(1),
                'reg_instance': re.search(r'name="reg_instance" value="(.*?)"', data).group(1),
                'reg_impression_id': re.search(r'name="reg_impression_id" value="(.*?)"', data).group(1)
            }
        except:
            UI.log("ERROR", "Failed to handshake. IP Blocked?", UI.RED)
            return

        fname, lname = self.faker.first_name(), self.faker.last_name()
        email, login, domain = TempMail.generate()
        password = self.faker.password(length=12)
        encpass = f"#PWD_BROWSER:0:{int(time.time())}:{password}"
        
        UI.log("INFO", f"Creating: {fname} {lname}", UI.WHITE)

        payload.update({
            'ccp': '2', 'submission_request': 'true', 'helper': '', 'ns': '1', 'app_id': '103',
            'firstname': fname, 'lastname': lname, 'reg_email__': email,
            'sex': random.choice(['1', '2']), 'reg_passwd__': password, 'encpass': encpass,
            'birthday_day': str(random.randint(1, 28)), 
            'birthday_month': str(random.randint(1, 12)),
            'birthday_year': str(random.randint(1998, 2005)),
            'submit': 'Sign Up'
        })

        try:
            resp = self.session.post(Config.SUBMIT_URL, data=payload)
            if "c_user" in self.session.cookies.get_dict():
                self.save(email, password, self.session.cookies.get_dict())
                UI.log("SUCCESS", "Account Created (No Checkpoint)!", UI.GREEN)
            elif "confirmemail" in resp.url:
                UI.log("WAIT", "Waiting for OTP...", UI.YELLOW)
                code = TempMail.get_code(login, domain)
                if code:
                    self.verify(code, email, password)
                else:
                    UI.log("FAIL", "OTP Timeout", UI.RED)
            else:
                UI.log("FAIL", "Registration rejected by Facebook", UI.RED)
        except Exception as e:
            UI.log("ERROR", str(e), UI.RED)

    def verify(self, code, email, password):
        data = {'c': code, 'submit': 'Confirm'}
        self.session.post("https://m.facebook.com/confirmemail.php", data=data)
        if "c_user" in self.session.cookies.get_dict():
            self.save(email, password, self.session.cookies.get_dict())
            UI.log("SUCCESS", "Verified Successfully!", UI.GREEN)
        else:
            UI.log("FAIL", "Checkpoint after verification", UI.RED)

    def save(self, email, password, cookies):
        c_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        path = os.path.join(Config.BASE_PATH, "FRAACCOUNT.txt")
        with open(path, "a") as f:
            f.write(f"{email}|{password}|{c_str}\n")

class FacebookManager:
    def get_tokens(self, file_key):
        file_name = Config.FILES.get(str(file_key))
        if not file_name: return []
        path = os.path.join(Config.BASE_PATH, file_name)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]
            tokens = []
            for line in lines:
                parts = line.split("|")
                for part in parts:
                    if part.startswith("EAA"):
                        tokens.append(part)
                        break
            return tokens
        except: return []

    def perform_action(self, token, target_id, action_type, extra_data=None):
        url = None
        data = {'access_token': token}
        headers = {'User-Agent': Utils.get_user_agent()}

        if action_type == "REACT":
            url = f'https://graph.facebook.com/{target_id}/reactions'
            data['type'] = extra_data.upper()
        elif action_type == "COMMENT":
            url = f'https://graph.facebook.com/{target_id}/comments'
            data['message'] = extra_data
        elif action_type == "SHARE":
            url = f'https://graph.facebook.com/me/feed'
            data['link'] = f"https://www.facebook.com/{target_id}"
            data['published'] = '1'
        elif action_type == "FOLLOW":
            url = f'https://graph.facebook.com/{target_id}/subscribers'

        try:
            if url:
                req = requests.post(url, data=data, headers=headers, timeout=10)
                return req.status_code == 200
        except: return False
        return False

    def login_extractor(self, email, password, save_key):
        data = {
            'method': 'auth.login',
            'fb_api_req_friendly_name': 'authenticate',
            'fb_api_caller_class': 'com.facebook.account.login.protocol.Fb4aAuthHandler',
            'api_key': Config.API_KEY,
            'email': email,
            'password': password,
            'access_token': Config.ACCESS_TOKEN_SEED
        }
        try:
            req = requests.post('https://b-graph.facebook.com/auth/login', data=data).json()
            if 'access_token' in req:
                token = req['access_token']
                path = os.path.join(Config.BASE_PATH, Config.FILES[str(save_key)])
                with open(path, 'a') as f:
                    f.write(f"{req['uid']}|{token}\n")
                return True
        except: pass
        return False

def menu_create():
    UI.banner()
    print(f"{UI.YELLOW}[!] TIPS: Use 4G Data. Turn Airplane Mode ON/OFF between accounts.")
    print(UI.LINE)
    try:
        amt = int(input(f"{UI.CYAN}Amount to create > {UI.RESET}"))
        creator = AccountCreator()
        for i in range(amt):
            print(f"\n{UI.WHITE}--- Account {i+1}/{amt} ---")
            creator.create()
            if i < amt - 1:
                print(f"{UI.CYAN}Cooling down (10s)...")
                time.sleep(10)
    except ValueError: pass
    input(f"\n{UI.WHITE}Press Enter...")

def menu_extract():
    UI.banner()
    print(f"{UI.YELLOW}Convert Email|Pass list to Access Tokens")
    path = input(f"{UI.CYAN}Path to list (email|pass) > {UI.RESET}")
    print("1. Save to FRAACCOUNT (Main)")
    print("2. Save to RPWACCOUNT (Alt)")
    key = input("Select > ")
    
    if os.path.exists(path):
        manager = FacebookManager()
        with open(path, 'r') as f:
            creds = [line.strip().split('|') for line in f if '|' in line]
        
        UI.log("START", f"Extracting {len(creds)} accounts...", UI.CYAN)
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(manager.login_extractor, c[0], c[1], key) for c in creds]
            for f in as_completed(futures):
                if f.result(): print(f"{UI.GREEN}.", end="", flush=True)
                else: print(f"{UI.RED}.", end="", flush=True)
        print("\nDone.")
    input(f"\n{UI.WHITE}Press Enter...")

def menu_boost():
    UI.banner()
    manager = FacebookManager()
    print(f"{UI.YELLOW}Select Token Source:")
    for k, v in Config.FILES.items(): print(f"[{k}] {v}")
    
    src = input(f"{UI.CYAN}Select > {UI.RESET}")
    tokens = manager.get_tokens(src)
    
    if not tokens:
        print(f"{UI.RED}No tokens found! Create or Extract first.")
        time.sleep(2)
        return

    print(UI.LINE)
    print(f"{UI.GREEN}Loaded {len(tokens)} Tokens")
    print(f"{UI.YELLOW}[1] React  [2] Comment  [3] Share  [4] Follow")
    
    act = input(f"{UI.CYAN}Action > {UI.RESET}")
    target = Utils.extract_id(input(f"{UI.WHITE}Link/ID > {UI.RESET}"))
    
    action_type, extra = "", None
    if act == '1':
        action_type = "REACT"
        print("TYPE: LIKE, LOVE, WOW, HAHA, SAD, ANGRY")
        extra = input("Type > ")
    elif act == '2':
        action_type = "COMMENT"
        extra = input("Comment > ")
    elif act == '3': action_type = "SHARE"
    elif act == '4': action_type = "FOLLOW"

    limit = int(input(f"{UI.WHITE}Amount > {UI.RESET}"))
    if limit > len(tokens): limit = len(tokens)

    UI.log("RUN", "Boosting started...", UI.CYAN)
    success = 0
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(manager.perform_action, tokens[i], target, action_type, extra) for i in range(limit)]
        for f in as_completed(futures):
            if f.result(): success += 1
            print(f"\r{UI.GREEN}Success: {success} / {limit}", end="")
            
    print("\n")
    input(f"{UI.WHITE}Press Enter...")

def main():
    Utils.ensure_files()
    while True:
        UI.banner()
        print(f"{UI.YELLOW}[1] Auto Creator (Reg)")
        print(f"{UI.YELLOW}[2] Token Extractor (Login)")
        print(f"{UI.YELLOW}[3] Boosting Menu")
        print(f"{UI.YELLOW}[4] Clear Data")
        print(f"{UI.YELLOW}[0] Exit")
        print(UI.LINE)
        
        sel = input(f"{UI.CYAN}Select > {UI.RESET}")
        
        if sel == '1': menu_create()
        elif sel == '2': menu_extract()
        elif sel == '3': menu_boost()
        elif sel == '4': 
            for f in Config.FILES.values():
                open(os.path.join(Config.BASE_PATH, f), 'w').close()
            print(f"{UI.GREEN}All data cleared.")
            time.sleep(1)
        elif sel == '0': sys.exit()

if __name__ == "__main__":
    main()
