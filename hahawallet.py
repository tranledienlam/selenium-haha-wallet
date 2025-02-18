
import random
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility

class HaHaWallet:
    def __init__(self, driver: webdriver.Chrome, profile) -> None:
        self.node = Node(driver, profile['profile'])
        self.driver = driver
        self.profile_name = profile['profile']
        self.pin = profile['pin']
        self.wallet = profile['wallet']
        self.url ='chrome-extension://andhndehpcjpmneneealacgnmealilal'
    
    def faucet_eth(self):
        Utility.wait_time(10)
        self.node.go_to('https://cloud.google.com/application/web3/faucet/ethereum/sepolia')
        self.node.find_and_input(By.CSS_SELECTOR, 'input[id="mat-input-0"]', self.wallet, 0, 5)
        self.node.find_and_click(By.XPATH, '//button[span[text()=" Receive 0.05 Sepolia ETH "]]')
        
    def unlock(self) -> bool:
        actions = [
            (self.node.go_to, self.url + '/home.html'),
            (self.node.find_and_input, By.CSS_SELECTOR, "input[type='password']", self.pin),
            (self.node.find_and_click, By.XPATH, "//button[text()='Unlock']")
        ]
        return self.node.execute_chain(actions=actions, message_error='unlock ví không thành công')

    def check_in(self) -> bool:
        actions = [
            (Utility.wait_time, 5),
            (self.node.go_to, self.url +'/home.html#quests'),
            (self.node.find_and_click, By.XPATH, '//button[text()="Claim"]')
        ]
        
        if self.node.execute_chain(actions=actions, message_error='Check-in gặp lỗi hoặc đã thực hiện'):
            self.node.log("check-in thành công")
            return True
        
        return False
    
    def send_eth(self) -> bool:
        random_eth = random.uniform(0.00001, 0.001)
        actions = [
            (Utility.wait_time, 5),
            (self.node.go_to, self.url + '/home.html'),
            (self.node.find_and_click, By.XPATH, '//button[p[text()="Send"]]'),
            (self.node.find_and_click, By.XPATH, '//div[p[text()="ETH"]]'),
            (self.node.find_and_click, By.XPATH, '//div[text()="Account 1 (Smart Wallet)"]'),
            (self.node.find_and_input, By.CSS_SELECTOR, 'input[type="text"]', str(random_eth)),
            (self.node.find_and_click, By.XPATH, '//button[text()="Next"]'),
            (self.node.find_and_click, By.XPATH, '//button[text()="Confirm"]'),
        ]
        return self.node.execute_chain(actions=actions, message_error='Send ETH thất bại')
    
    def _run_logic(self):
        self.faucet_eth()
        if self.unlock():
            self.check_in()
            for _ in range(10):
                if self.send_eth():
                    continue
                else:
                    self.node.stop()
            Utility.wait_time(5)
        else:
            self.node.stop()
        Utility.wait_time(5)    
        

class Main:
    def __init__(self, driver, profile) -> None:
        self.profile = profile
        self.driver = driver

    def _run(self):
        HaHaWallet(self.driver, self.profile)._run_logic()


if __name__ == '__main__':
    DATA_DIR = Path(__file__).parent/'data.txt'

    if not DATA_DIR.exists():
        print(f"File {DATA_DIR} không tồn tại. Dừng mã.")
        exit()

    PROFILES = []
    num_parts = 3

    with open(DATA_DIR, 'r') as file:
        data = file.readlines()

    for line in data:
        parts = line.strip().split('|')

        if len(parts) != num_parts:
            print(f"Warning: Dữ liệu không hợp lệ - {line}")
            continue

        profile, wallet, pin, *_ = (parts + [None] * num_parts)[:num_parts]

        PROFILES.append({
            'profile': profile,
            'wallet':wallet,
            'pin': pin,
        })

    manager = BrowserManager(Main)
    manager.config_extension('HaHa-Wallet-Chrome-Web-Store.crx')
    # manager.run_browser(profile=PROFILES[0])
    manager.run_terminal(
        profiles=PROFILES,
        auto=False,
        max_concurrent_profiles=4
    )
