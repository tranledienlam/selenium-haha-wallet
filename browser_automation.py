import requests
import sys
from pathlib import Path
from io import BytesIO
from math import ceil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException, ElementNotVisibleException
from screeninfo import get_monitors

from utils import Utility


class Node:
    def __init__(self, driver: webdriver.Chrome, profile_name: str) -> None:
        '''
        Khởi tạo một đối tượng Node để quản lý và thực hiện các tác vụ tự động hóa trình duyệt.

        Args:
            driver (webdriver.Chrome): WebDriver điều khiển trình duyệt Chrome.
            profile_name (str): Tên profile được sử dụng để khởi chạy trình duyệt
        '''
        self._driver = driver
        self.profile_name = profile_name
        # Khoảng thời gian đợi mặc định giữa các hành động (giây)
        self.wait = 5
        self.timeout = 20  # Thời gian chờ mặc định (giây) cho các thao tác

    def _execute_node(self, node_action, *args):
        """
        Thực hiện một hành động node bất kỳ.
        Đây là function hỗ trợ thực thi node cho execute_chain

        Args:
            node_action: tên node
            *args: arg được truyền vào node
        """
        if not node_action(*args):
            return False
        return True

    def execute_chain(self, actions: list[tuple], message_error: str = 'Dừng thực thi chuỗi hành động'):
        """
        Thực hiện chuỗi các node hành động. 
        Dừng lại nếu một node thất bại.

        Args:
            actions (list[tuple]): Danh sách các tuple đại diện cho các hành động.
                Mỗi tuple có cấu trúc: 
                    (hàm_thực_thi, *tham_số_cho_hàm)
                Trong đó:
                    - `hàm_thực_thi` là một hàm được định nghĩa trong class, chịu trách nhiệm thực hiện hành động.
                    - `*tham_số_cho_hàm` là danh sách các tham số sẽ được truyền vào `hàm_thực_thi`.
                    - `stop_on_failure` (bool): Nếu False, không dừng chuỗi hành động dù hành động hiện tại thất bại. Mặc định là True

            message_error (str): Thông báo lỗi khi xảy ra thất bại trong chuỗi hành động.

        Returns:
            bool: 
                - `True` nếu tất cả các hành động đều được thực thi thành công.
                - `False` nếu có bất kỳ hành động nào thất bại.    

        Ví dụ: 
            actions = [
                (find, By.ID, 'onboarding__terms-checkbox', False), # Nếu lỗi vẫn tiếp tục
                (find_and_input, By.CSS_SELECTOR, 'button[data-testid="onboarding-import-wallet"]', False),
                (find_and_click, By.ID, 'metametrics-opt-in'),
                (find_and_click, By.CSS_SELECTOR, 'button[data-testid="metametrics-i-agree"]')
            ]

            self.execute_chain(actions, message_error="Lỗi trong quá trình thực hiện chuỗi hành động.")
        """
        for action in actions:
            *action_args, stop_on_failure = action if len(
                action) > 2 and isinstance(action[-1], bool) else (*action, True)

            if not self._execute_node(action_args[0], *action_args[1:]):
                self.log(
                    f'Lỗi {["skip "] if not stop_on_failure else ""}- {message_error}')
                if stop_on_failure:
                    return False

        return True

    def log(self, message: str = 'message chưa có mô tả'):
        '''
        Ghi và hiển thị thông báo nhật ký (log)

        Cấu trúc log hiển thị:
            [profile_name][func_thuc_thi]: {message}

        Args:
            message (str, option): Nội dung thông báo log. Mặc định là 'message chưa có mô tả'.

        Mô tả:
            - Phương thức sử dụng tiện ích `Utility.logger` để ghi lại thông tin nhật ký kèm theo tên hồ sơ (`profile_name`) của phiên làm việc hiện tại.
        '''
        Utility.logger(self.profile_name, message)

    def stop(self, message: str = 'Dừng thực thi.'):
        '''
        Phương thức dừng thực thi và quăng lỗi ra ngoài.

        Args:
            message (str, option): Thông điệp mô tả lý do dừng thực thi. Mặc định là 'Dừng thực thi.'.

        Mô tả:
            Phương thức này sẽ ghi lại thông điệp dừng thực thi qua log, sau đó quăng ra một lỗi `ValueError` với thông điệp tương ứng.
            Khi được gọi, phương thức sẽ ngừng các hành động tiếp theo trong chương trình.
        '''
        self.log(message)
        raise ValueError(f'{message}')

    def go_to(self, url: str, wait: int = None, timeout: int = None):
        '''
        Điều hướng trình duyệt đến một URL cụ thể và chờ trang tải hoàn tất.

        Args:
            url (str): URL đích cần điều hướng đến.
            wait (int, optional): Thời gian chờ trước khi điều hướng, mặc định là giá trị của `self.wait = 5`.
            timeout (int, optional): Thời gian chờ tải trang, mặc định là giá trị của `self.timeout`.

        Returns:
            bool:
                - `True`: nếu trang tải thành công.
                - `False`: nếu có lỗi xảy ra trong quá trình tải trang.
        '''
        timeout = timeout if timeout else self.timeout
        wait = wait if wait else self.wait

        Utility.wait_time(wait)
        try:
            # self._driver.get(url)
            self._driver.execute_script(f"window.location.href = '{url}';")

            WebDriverWait(self._driver, timeout).until(
                lambda driver: driver.execute_script(
                    "return document.readyState") == 'complete'
            )
            self.log(f'Trang {url} đã tải thành công.')
            return True

        except Exception as e:
            self.log(f'Lỗi - Khi tải trang "{url}": {e}')

        return False

    def get_url(self, wait: int = None):
        '''
        Phương thức lấy url hiện tại

        Args:
            wait (int, optional): Thời gian chờ trước khi điều hướng, mặc định là giá trị của `self.wait = 5`.

        Returns:
            Chuỗi str URL hiện tại
        '''
        wait = wait if wait else self.wait

        Utility.wait_time(wait, True)
        return self._driver.current_url

    def find(self, by: By | str, value: str, wait: int = None, timeout: int = None):
        '''
        Phương thức tìm một phần tử trên trang web trong khoảng thời gian chờ cụ thể.

        Args:
            by (By|str): Kiểu định vị phần tử (ví dụ: By.ID, By.CSS_SELECTOR, By.XPATH).
            value (str): Giá trị tương ứng với phương thức tìm phần tử (ví dụ: tên ID, đường dẫn XPath, v.v.).
            wait (int, optional): Thời gian chờ trước khi điều hướng, mặc định là giá trị của `self.wait = 5`.
            timeout (int, optional): Thời gian tối đa chờ phần tử xuất hiện (đơn vị: giây). Mặc định sử dụng giá trị `self.timeout`.

        Returns:
            WebElement | bool:
                - WebElement: nếu tìm thấy phần tử.
                - `None`: nếu không tìm thấy hoặc xảy ra lỗi.
        '''
        timeout = timeout if timeout else self.timeout
        wait = wait if wait else self.wait
        Utility.wait_time(wait)
        try:
            element = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.log(f'Tìm thấy phần tử {by}={value}')
            return element

        except TimeoutException:
            self.log(
                f'Lỗi - Không tìm thấy phần tử {by}={value} trong {timeout}s')
        except StaleElementReferenceException:
            self.log(
                f'Lỗi - Phần tử {by}={value} đã bị thay đổi hoặc bị loại bỏ khỏi DOM')
        except Exception as e:
            self.log(f'Lỗi - không xác định khi tìm phần tử {by}={value} {e}')

        return None

    def find_and_click(self, by: By | str, value: str, wait: int = None, timeout: int = None) -> bool:
        '''
        Phương thức tìm và nhấp vào một phần tử trên trang web.

        Args:
            by (By | str): Kiểu định vị phần tử (ví dụ: By.ID, By.CSS_SELECTOR, By.XPATH).
            value (str): Giá trị tương ứng với phương thức tìm phần tử (ví dụ: tên ID, đường dẫn XPath, v.v.).
            wait (int, option): Thời gian chờ trước khi thực hiện thao tác nhấp. Mặc định sử dụng giá trị `self.wait = 5`.
            timeout (int, option): Thời gian tối đa để chờ phần tử có thể nhấp được. Mặc định sử dụng giá trị `self.timeout`.

        Returns:
            bool: 
                `True`: nếu nhấp vào phần tử thành công.
                `False`: nếu gặp lỗi.

        Mô tả:
            - Phương thức sẽ tìm phần tử theo phương thức `by` và `value`.
            - Sau khi tìm thấy phần tử, phương thức sẽ đợi cho đến khi phần tử có thể nhấp được (nếu cần).
            - Sau khi phần tử có thể nhấp, sẽ tiến hành nhấp vào phần tử đó.
            - Nếu gặp lỗi, sẽ ghi lại thông báo lỗi cụ thể.
            - Nếu gặp lỗi liên quan đến Javascript (LavaMoat), phương thức sẽ thử lại bằng cách tìm phần tử theo cách khác.
        '''
        timeout = timeout if timeout else self.timeout
        wait = wait if wait else self.wait

        try:
            element = WebDriverWait(self._driver, timeout). until(
                EC.element_to_be_clickable((by, value))
            )
            Utility.wait_time(wait)
            element.click()
            self.log(f'Click phần tử {by}={value} thành công')
            return True

        except TimeoutException:
            self.log(
                f'Lỗi - Không tìm thấy phần tử {by}={value} trong {timeout}s')
        except StaleElementReferenceException:
            self.log(
                f'Lỗi - Phần tử {by}={value} đã thay đổi hoặc không còn hợp lệ')
        except ElementClickInterceptedException:
            self.log(
                f'Lỗi - Không thể nhấp vào phần tử phần tử {by}={value} vì bị che khuất hoặc ngăn chặn')
        except ElementNotInteractableException:
            self.log(
                f'Lỗi - Phần tử {by}={value} không thể tương tác, có thể bị vô hiệu hóa hoặc ẩn')
        except Exception as e:
            # Thử phương pháp click khác khi bị lỗi từ Javascript
            if 'LavaMoat' in str(e):
                element = WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                Utility.wait_time(wait)
                element.click()
                self.log(f'Click phần tử {by}={value} thành công (PT2)')
                return True
            else:
                self.log(f'Lỗi - Không xác định {by}={value} {e}')

        return False

    def find_and_input(self, by: By | str, value: str, text: str, delay: float = 0.2, wait: int = None, timeout: int = None):
        '''
        Phương thức tìm và điền văn bản vào một phần tử trên trang web.

        Args:
            by (By | str): Kiểu định vị phần tử (ví dụ: By.ID, By.CSS_SELECTOR, By.XPATH).
            value (str): Giá trị tương ứng với phương thức tìm phần tử (ví dụ: tên ID, đường dẫn XPath, v.v.).
            text (str): Nội dung văn bản cần nhập vào phần tử.
            delay (float): Thời gian trễ giữa mỗi ký tự khi nhập văn bản. Mặc định là 0.2 giây.
            wait (int, option): Thời gian chờ trước khi thực hiện thao tác nhấp. Mặc định sử dụng giá trị `self.wait = 5`.
            timeout (int, option): Thời gian tối đa để chờ phần tử có thể nhấp được. Mặc định sử dụng giá trị `self.timeout`.

        Returns:
            bool: 
                `True`: nếu nhập văn bản vào phần tử thành công.
                `False`: nếu gặp lỗi trong quá trình tìm hoặc nhập văn bản.

        Mô tả:
            - Phương thức sẽ tìm phần tử theo phương thức `by` và `value`.
            - Sau khi tìm thấy phần tử và đảm bảo phần tử có thể tương tác, phương thức sẽ thực hiện nhập văn bản `text` vào phần tử đó.
            - Văn bản sẽ được nhập từng ký tự một, với thời gian trễ giữa mỗi ký tự được xác định bởi tham số `delay`.
            - Nếu gặp lỗi, sẽ ghi lại thông báo lỗi cụ thể.
            - Nếu gặp lỗi liên quan đến Javascript (LavaMoat), phương thức sẽ thử lại bằng cách tìm phần tử theo cách khác.
        '''
        timeout = timeout if timeout else self.timeout
        wait = wait if wait else self.wait

        try:
            element = WebDriverWait(self._driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            Utility.wait_time(wait)
            for char in text:
                Utility.wait_time(delay)
                element.send_keys(char)
            self.log(f'Nhập văn bản phần tử {by}={value} thành công')
            return True

        except TimeoutException:
            self.log(
                f'Lỗi - Không tìm thấy phần tử {by}={value} trong {timeout}s')
        except StaleElementReferenceException:
            self.log(
                f'Lỗi - Phần tử {by}={value} đã bị thay đổi hoặc bị loại bỏ khỏi DOM')
        except ElementNotVisibleException:
            self.log(
                f'Lỗi - Phần tử {by}={value} có trong DOM nhưng không nhìn thấy. ví dụ display: none hoặc visibility: hidden')
        except Exception as e:
            # Thử phương pháp click khác khi bị lỗi từ Javascript
            if 'LavaMoat' in str(e):
                element = WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                Utility.wait_time(wait)
                for char in text:
                    Utility.wait_time(delay)
                    element.send_keys(char)
                self.log(f'Nhập văn bản phần tử {by}={value} thành công (PT2)')
                return True
            else:
                self.log(f'Lỗi - không xác định {by}={value} {e}')

        return False

    def get_text(self, by, value, wait=None, timeout=None):
        '''
        Phương thức tìm và lấy văn bản từ một phần tử trên trang web.

        Args:
            by (By | str): Phương thức xác định cách tìm phần tử (ví dụ: By.ID, By.CSS_SELECTOR, By.XPATH).
            value (str): Giá trị tương ứng với phương thức tìm phần tử (ví dụ: ID, đường dẫn XPath, v.v.).
            wait (int, option): Thời gian chờ trước khi thực hiện thao tác lấy văn bản, mặc định sử dụng giá trị `self.wait = 5`.
            timeout (int, option): Thời gian tối đa để chờ phần tử hiển thị, mặc định sử dụng giá trị `self.timeout`.

        Returns:
            str: Văn bản của phần tử nếu lấy thành công.
            `None`: Nếu không tìm thấy phần tử hoặc gặp lỗi.

        Mô tả:
            - Phương thức tìm phần tử trên trang web theo `by` và `value`.
            - Sau khi đảm bảo phần tử tồn tại, phương thức sẽ lấy văn bản từ phần tử và loại bỏ khoảng trắng thừa bằng phương thức `strip()`.
            - Nếu phần tử chứa văn bản, phương thức trả về văn bản đó và ghi log thông báo thành công.
            - Nếu gặp lỗi liên quan đến Javascript (LavaMoat), phương thức sẽ thử lại bằng cách tìm phần tử theo cách khác.
        '''
        timeout = timeout if timeout else self.timeout
        wait = wait if wait else self.wait

        try:
            element = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            Utility.wait_time(wait)
            text = element.text.strip()

            if text:
                self.log(f'Tìm thấy văn bản trong phần tử {by}={value}')
                return text
            else:
                self.log(f'Lỗi - Phần tử {by}={value} không chứa văn bản')

        except TimeoutException:
            print(
                f'[{self.profile_name}][get_text]: Lỗi - Không tìm thấy phần tử {by}={value} trong {timeout}s')
        except StaleElementReferenceException:
            print(
                f'[{self.profile_name}][get_text]: Lỗi - Phần tử {by}={value} đã bị thay đổi hoặc bị loại bỏ khỏi DOM')
        except Exception as e:
            self.log(
                f'Lỗi - Không xác định khi tìm văn bản trong phần tử {by}={value}')

        return None

    def check_window_handles(self):
        Utility.wait_time(5, True)
        original_handle = self._driver.current_window_handle
        window_handles = self._driver.window_handles

        print("Danh sách các cửa sổ/tab đang hoạt động:", window_handles)
        # handle là ID, ví dụ có 2 page ['433E0A85799F602DFA5CE74CA1D00682', '2A6FD93FC931056CCF842DF11782C45B']
        for handle in self._driver.window_handles:
            self._driver.switch_to.window(handle)
            print(f'{self._driver.title} - {self._driver.current_url}')

        self._driver.switch_to.window(original_handle)


class BrowserManager:
    def __init__(self, HandlerClass=None) -> None:
        self.HandlerClass = HandlerClass

        self.user_data_dir = Path(__file__).parent/'user_data'
        self.data_tele = self._get_telegram_credentials()
        self.matrix = [[None]]
        self.extensions = []

        monitors = get_monitors()
        # print(monitors)
        select_monitor = monitors[1]
        self.screen_width = select_monitor.width
        self.screen_height = select_monitor.height
        self.screen_x = select_monitor.x
        self.screen_y = select_monitor.y

    def _log(self, profile_name: str = 'SYS', message: str = 'message chưa có mô tả'):
        '''
        Ghi và hiển thị thông báo nhật ký (log)

        Cấu trúc log hiển thị:
            [profile_name][func_thuc_thi]: {message}

        Args:
            profile_name (str): tên hồ sơ hiện tại
            message (str, option): Nội dung thông báo log. Mặc định là 'message chưa có mô tả'.

        Mô tả:
            - Phương thức sử dụng tiện ích `Utility.logger` để ghi lại thông tin nhật ký kèm theo tên hồ sơ (`profile_name`) của phiên làm việc hiện tại.
        '''
        Utility.logger(profile_name, message)

    def _save_screenshot(self, driver, profile_name):
        snapshot_dir = Path(__file__).parent / 'snapshot'

        if not snapshot_dir.exists():
            self._log(profile_name,
                      f'Không tin thấy thư mục {snapshot_dir}. Đang tạo...')
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            self._log(profile_name, f'Tạo thứ mục Snapshot thành công')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = snapshot_dir/f'{profile_name}_{timestamp}.png'
        driver.save_screenshot(str(screenshot_path))

    def _send_screenshot_to_telegram(self, driver: webdriver.Chrome, profile_name: str, message: str):
        chat_id, telegram_token = self.data_tele
        # Tạo URL gửi ảnh qua Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"

        # Chụp ảnh màn hình và lưu vào bộ nhớ
        screenshot_png = driver.get_screenshot_as_png()
        screenshot_buffer = BytesIO(screenshot_png)
        screenshot_buffer.seek(0)  # Đặt con trỏ về đầu tệp

        # Gửi ảnh lên Telegram
        timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        files = {'photo': ('screenshot.png', screenshot_buffer, 'image/png')}
        data = {'chat_id': chat_id,
                'caption': f'[{timestamp}][{profile_name}] - {message}'}
        response = requests.post(url, files=files, data=data)

        # Kiểm tra kết quả
        if response.status_code == 200:
            self._log(profile_name, f'Hình ảnh lỗi được gửi đến bot tele')
        else:
            self._log(
                profile_name,
                f'Không thể gửi "Hình ảnh lỗi" lên Telegram. Mã lỗi: {response.status_code}. Lưu về local'
            )
            self._save_screenshot(driver, profile_name)
        # Đóng buffer sau khi sử dụng
        screenshot_buffer.close()

    def _get_telegram_credentials(self):
        """
        Lấy thông tin token Telegram và chat ID từ tệp cấu hình.

        Tệp cấu hình `token_tele.txt` phải nằm trong cùng thư mục với tệp mã nguồn, 
        và nội dung tệp phải có định dạng: `chat_id|telegram_token`.

        Returns:
            tuple: Gồm hai phần tử (chat_id, telegram_token) nếu tệp tồn tại và hợp lệ.
            None: Nếu tệp không tồn tại hoặc nội dung không hợp lệ.

        Ghi chú:
            - Nếu tệp không tồn tại, sẽ ghi log thông báo và trả về None.
            - Nếu nội dung tệp không hợp lệ (không chứa ký tự `|`), sẽ trả về None.
        """
        config_path = Path(__file__).parent / 'token_tele.txt'

        if config_path.exists():
            try:
                with open(config_path, 'r') as file:
                    data = file.readline().strip()

                if '|' in data:
                    # Chỉ chia đôi theo lần đầu tiên gặp `|`
                    chat_id, telegram_token = data.split('|', 1)
                    return chat_id, telegram_token
                else:
                    Utility.logger(
                        message=f'Nội dung tệp {config_path} không hợp lệ. Định dạng phải là "chat_id|telegram_token".')
                    return None
            except Exception as e:
                Utility.logger(message=f'Lỗi khi đọc tệp {config_path}: {e}')
                return None
        else:
            Utility.logger(
                message=f'Tệp {config_path} không tồn tại. Hình ảnh sẽ được lưu vào thư mục "snapshot".')
            return None

    def _get_matrix(self, number_profiles: int, max_concurrent_profiles: int):
        """
        Phương thức tạo ma trận vị trí cho các trình duyệt dựa trên số lượng hồ sơ và luồng song song tối đa.

        Args:
            number_profiles (int): Tổng số lượng hồ sơ cần chạy.
            max_concurrent_profiles (int): Số lượng hồ sơ chạy đồng thời tối đa.

        Hoạt động:
            - Nếu chỉ có 1 hồ sơ chạy, tạo ma trận 1x1.
            - Tự động điều chỉnh số hàng và cột dựa trên số lượng hồ sơ thực tế và giới hạn luồng song song.
            - Đảm bảo ma trận không dư thừa hàng/cột khi số lượng hồ sơ nhỏ hơn giới hạn song song.
        """
        # Số lượng hàng dựa trên giới hạn song song
        rows = 1 if max_concurrent_profiles == 1 else 2

        # Tính toán số cột cần thiết
        if number_profiles <= max_concurrent_profiles:
            # Dựa trên số lượng hồ sơ thực tế
            cols = ceil(number_profiles / rows)
        else:
            # Dựa trên giới hạn song song
            cols = ceil(max_concurrent_profiles / rows)

        # Tạo ma trận với số hàng và cột đã xác định
        self.matrix = [[None for _ in range(cols)] for _ in range(rows)]

    def _arrange_window(self, driver, row, col):
        cols = len(self.matrix[0])
        y = row * self.screen_height

        if cols > 1 and (cols * self.screen_width) > self.screen_width*2:
            x = col * (self.screen_width // (cols-1))
        else:
            x = col * self.screen_width
        driver.set_window_rect(x, y, self.screen_width, self.screen_height)

    def _get_position(self, profile_name: int):
        """
        Gán profile vào một ô trống và trả về tọa độ (x, y).
        """
        for row in range(len(self.matrix)):
            for col in range(len(self.matrix[0])):
                if self.matrix[row][col] is None:
                    self.matrix[row][col] = profile_name
                    return row, col
        return None, None

    def _release_position(self, profile_name: int, row, col):
        """
        Giải phóng ô khi profile kết thúc.
        """
        for row in range(len(self.matrix)):
            for col in range(len(self.matrix[0])):
                if self.matrix[row][col] == profile_name:
                    self.matrix[row][col] = None
                    return True
        return False

    def _browser(self, profile_name: str) -> webdriver.Chrome:
        '''
        Phương thức khởi tạo trình duyệt Chrome (browser) với các cấu hình cụ thể, tự động khởi chạy khi gọi `BrowserManager.run_browser()`.

        Args:
            profile_name (str): tên hồ sơ. Được tự động thêm vào khi chạy phương thức `BrowserManager.run_browser()`

        Returns:
            driver (webdriver.Chrome): Đối tượng trình duyệt được khởi tạo.

        Mô tả:
            - Dựa trên thông tin hồ sơ (`profile_data`), hàm sẽ thiết lập và khởi tạo trình duyệt Chrome với các tùy chọn cấu hình sau:
                - Chạy browser với dữ liệu người dùng (`--user-data-dir`).
                - Tùy chọn tỉ lệ hiển thị trình duyệt (`--force-device-scale-factor`)
                - Tắt các thông báo tự động và hạn chế các tính năng tự động hóa của trình duyệt.
                - Vô hiệu hóa dịch tự động của Chrome.
                - Vô hiệu hóa tính năng lưu mật khẩu (chỉ áp dụng khi sử dụng hồ sơ mặc định).
            - Các tiện ích mở rộng (extensions) được thêm vào trình duyệt (Nếu có).       
        '''
        rows = len(self.matrix)
        scale = 1 if (rows == 1) else 0.5

        self._log(profile_name, 'Đang mở')

        chrome_options = ChromeOptions()

        chrome_options.add_argument(
            f'--user-data-dir={self.user_data_dir}/{profile_name}')
        # chrome_options.add_argument(f'--profile-directory={profile_name}') # tắt để sử dụng profile defailt trong profile_name
        chrome_options.add_argument('--disable-blink-features=AutomationControlled') # để có thể đăng nhập google
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument(f"--force-device-scale-factor={scale}")
        chrome_options.add_argument(
            "--disable-features=Translate")  # Vô hiệu hóa translate
        # Tắt dòng thông báo auto
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])

        # vô hiệu hóa save mật khẩu
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False
        })  # chỉ dùng được khi dùng profile default (tắt --profile-directory={profile_name})

        # add extensions
        for ext in self.extensions:
            chrome_options.add_extension(ext)

        service = Service(log_path='NUL')

        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver

    def config_extension(self, *args: str):
        '''
        Cấu hình trình duyệt với các tiện ích mở rộng (extensions).

        Args:
            *args (str): Danh sách tên tệp các tiện ích mở rộng (ví dụ: 'ext1.crx', 'ext2.crx').

        Mô tả:
            - Phương thức sẽ kiểm tra sự tồn tại của từng tệp tiện ích mở rộng được cung cấp trong tham số `args`.
            - Đường dẫn của các tiện ích mở rộng sẽ được xác định dựa trên thư mục `extensions` nằm cùng cấp với tệp hiện tại (`__file__`).
            - Nếu bất kỳ tệp tiện ích mở rộng nào không tồn tại, phương thức sẽ thông báo lỗi và dừng chương trình.
            - Nếu tất cả các tệp tồn tại, chúng sẽ được thêm vào danh sách `self.extensions` để sử dụng trước khi khởi chạy trình duyệt.

        Ví dụ:
            config_extension('ext1.crx', 'ext2.crx')
        '''
        for arg in args:
            ext = Path(__file__).parent/'extensions'/f'{arg}'
            if not ext.exists():
                self._log(f'Lỗi: {ext} không tồn tại. Dừng chương trình')
                exit()
            self.extensions.append(ext)
            
    def _listen_for_enter(self, profile_name: str):
        """Lắng nghe sự kiện Enter để dừng trình duyệt"""
        if sys.stdin.isatty():  # Kiểm tra nếu có stdin hợp lệ
            input(f"[{profile_name}] Nhấn ENTER để đóng trình duyệt...")
        else:
            print(f"[{profile_name}] ⚠ Không thể sử dụng input() trong môi trường này. Đóng tự động sau 10 giây.")
            Utility.wait_time(10)
    
    def run_browser(self, profile: dict, row: int = 0, col: int = 0, stop_flag: any = None):
        '''
        Phương thức khởi chạy trình duyệt (browser).

        Args:
            profile (dict): Thông tin cấu hình hồ sơ trình duyệt
                - profile_name (str): Tên hồ sơ trình duyệt.
            row (int, option): Vị trí hàng để sắp xếp cửa sổ trình duyệt. Mặc định là 0.
            col (int, option): Vị trí cột để sắp xếp cửa sổ trình duyệt. Mặc định là 0.
            stop_flag (multiprocessing.Value, option): Cờ tín hiệu để dừng trình duyệt. 
                - Nếu `stop_flag` là `True`, trình duyệt sẽ duy trì trạng thái trước khi enter.
                - Nếu là `None|False`, trình duyệt sẽ tự động đóng sau khi chạy xong.

        Mô tả:
            - Hàm khởi chạy trình duyệt dựa trên thông tin hồ sơ (`profile`) được cung cấp.
            - Sử dụng phương thức `_browser` để khởi tạo đối tượng trình duyệt (`driver`).
            - Gọi phương thức `_arrange_window` để sắp xếp vị trí cửa sổ trình duyệt theo `row` và `col`.
            - Nếu `HandlerClass` được chỉ định, phương thức `run` của lớp này sẽ được gọi để xử lý thêm logic.
            - Nêu `stop_flag` được cung cấp, trình duyệt sẽ duy trì hoạt động cho đến khi nhấn enter.
            - Sau cùng, - Đóng trình duyệt và giải phóng vị trí đã chiếm dụng bằng `_release_position`.

        Lưu ý:
            - Phương thức này có thể chạy độc lập hoặc được gọi bên trong `BrowserManager.run_multi()` và `BrowserManager.run_stop()`.
            - Đảm bảo rằng `HandlerClass` (nếu có) được định nghĩa với phương thức `run_browser()`.
        '''
        profile_name = profile['profile']
        driver = self._browser(profile_name)
        self._arrange_window(driver, row, col)
        
        try:
            # Khi chạy chương trình với phương thức run_stop. Duyệt trình sẽ duy trì trạng thái
            if stop_flag:
                self._listen_for_enter(profile_name)
            
            # Thực thi logic bên ngoài khi đồng thời có HandlerClass và không chạy run_stop()
            if self.HandlerClass and not stop_flag:
                self.HandlerClass(driver, profile)._run()
                

        except Exception as e:
            Utility.wait_time(5, True)
            if self.data_tele:
                self._send_screenshot_to_telegram(driver, profile_name, e)
            else:
                self._save_screenshot(driver, profile_name)

        finally:
            self._log(profile_name, 'Đóng... wait')
            Utility.wait_time(1, True)
            driver.quit()
            self._release_position(profile_name, row, col)

    def run_multi(self, profiles: list[dict], max_concurrent_profiles: int = 1, delay_between_profiles: int = 10):
        '''
        Phương thức khởi chạy nhiều hồ sơ đồng thời

        Args:
            profiles (list[dict]): Danh sách các hồ sơ trình duyệt cần khởi chạy.
                Mỗi hồ sơ là một dictionary chứa thông tin, với key 'profile' là bắt buộc, ví dụ: {'profile': 'profile_name',...}.
            max_concurrent_profiles (int, option): Số lượng tối đa các hồ sơ có thể chạy đồng thời. Mặc định là 1.
            delay_between_profiles (int, option): Thời gian chờ giữa việc khởi chạy hai hồ sơ liên tiếp (tính bằng giây). Mặc định là 10 giây.

        Hoạt động:
            - Sử dụng `ThreadPoolExecutor` để khởi chạy các hồ sơ trình duyệt theo mô hình đa luồng.
            - Hàng đợi (`queue`) chứa danh sách các hồ sơ cần chạy.
            - Xác định vị trí hiển thị trình duyệt (`row`, `col`) thông qua `_get_position`.
            - Khi có vị trí trống, hồ sơ sẽ được khởi chạy thông qua phương thức `run`.
            - Nếu không có vị trí nào trống, chương trình chờ 10 giây trước khi kiểm tra lại.
        '''
        queue = [profile for profile in profiles]
        self._get_matrix(max_concurrent_profiles, len(queue))

        with ThreadPoolExecutor(max_workers=max_concurrent_profiles) as executor:
            while len(queue) > 0:
                profile = queue[0]
                profile_name = profile['profile']
                row, col = self._get_position(profile_name)

                if row is not None and col is not None:
                    queue.pop(0)
                    executor.submit(self.run_browser, profile, row, col)
                    # thời gian chờ mở profile kế
                    Utility.wait_time(delay_between_profiles, True)
                else:
                    # thời gian chờ mở profile kế# Thời gian chờ check lại
                    Utility.wait_time(10, True)

    def run_stop(self, profiles: list[dict]):
        '''
        Chạy từng hồ sơ trình duyệt tuần tự, đảm bảo chỉ mở một profile tại một thời điểm.

        Args:
            profiles (list[dict]): Danh sách các hồ sơ trình duyệt cần khởi chạy.
                Mỗi profile là một dictionary chứa thông tin, trong đó key 'profile' là bắt buộc. 
                Ví dụ: {'profile': 'profile_name', ...}
                
        Hoạt động:
            - Duyệt qua từng profile trong danh sách.
            - Hiển thị thông báo chờ 5 giây trước khi khởi chạy từng hồ sơ.
            - Gọi `run_browser()` để chạy hồ sơ.
            - Chờ cho đến khi hồ sơ hiện tại đóng lại trước khi tiếp tục hồ sơ tiếp theo.
        '''
        
        for index, profile in enumerate(profiles):
            self._log(profile_name=profile['profile'], message=f'[{index+1}/{len(profiles)}]Chờ 5s...')
            Utility.wait_time(5)
            
            self.run_browser(profile=profile, stop_flag=True)

    def run_terminal(self, profiles: list[dict], auto : bool = False, max_concurrent_profiles: int = 4):
        '''
        Chạy giao diện dòng lệnh để người dùng chọn chế độ chạy.

        Args:
            profiles (list[dict]): Danh sách các profile trình duyệt có thể khởi chạy.
                Mỗi profile là một dictionary chứa thông tin, trong đó key 'profile' là bắt buộc. 
                Ví dụ: {'profile': 'profile_name', ...}
            auto (bool, option):
                True, bỏ qua lựa chọn terminal và chạy trực tiếp chức năng auto. Giá trị mặc định False
            max_concurrent_profiles (int, option): 
                Số lượng tối đa các hồ sơ có thể chạy đồng thời. Mặc định là 4.
        
        Chức năng:
            - Hiển thị menu cho phép người dùng chọn một trong các chế độ:
                1. Set up: Chọn và mở lần lượt từng profile để cấu hình.
                2. Chạy auto: Tự động chạy các profile đã cấu hình.
                0. Thoát chương trình.
            - Khi chọn Set up, người dùng có thể chọn chạy tất cả hoặc chỉ một số profile cụ thể.
            - Khi chọn Chạy auto, chương trình sẽ khởi động tự động với số lượng profile tối đa có thể chạy đồng thời.
            - Hỗ trợ quay lại menu chính hoặc thoát chương trình khi cần.
        
        Hoạt đông:
            - Gọi `run_stop()` nếu người dùng chọn Set up.
            - Gọi `run_multi()` nếu người dùng chọn Chạy auto.
        '''
        is_run = True
        while is_run:
            
            if not auto:
                print("\n[A]. Chọn một tùy chọn:")
                print("1. Set up (mở lần lượt từng profile để cấu hình)")
                print("2. Chạy auto (tất cả profiles sau khi đã cấu hình)")
                print("0. Thoát")
                choice = input("Nhập lựa chọn: ")
            else:
                choice = '2'
                is_run = False
                
                
            if choice in ('1', '2'):
                
                if not auto:
                    print(f"[B]. Chọn các profile muốn chạy {'Set up' if choice == '1' else 'Auto'}:")
                    print("0. ALL")
                    for idx, profile in enumerate(profiles, start=1):
                        print(f"{idx}. {profile['profile']}")
                
                    profile_choice = input("Nhập số và cách nhau bằng dấu cách (nếu chọn nhiều) hoặc 'back'|'b' để quay lại: ")
                else:
                    profile_choice = '0'
                
                if profile_choice.lower() in ["back", "b"]:
                    continue
                
                selected_profiles = []
                choices = profile_choice.split()
                if "0" in choices:  # Chạy tất cả profiles
                    selected_profiles = profiles
                else:
                    for ch in choices:
                        if ch.isdigit():
                            index = int(ch) - 1
                            if 0 <= index < len(profiles):  # Kiểm tra index hợp lệ
                                selected_profiles.append(profiles[index])
                            else:
                                print(f"⚠ Profile {ch} không hợp lệ, bỏ qua.")
                                
                if not selected_profiles:
                    print("Lựa chọn không hợp lệ. Vui lòng thử lại.")
                    continue
                
                if choice == '1':
                    self.run_stop(selected_profiles)
                else:
                    self.run_multi(profiles=selected_profiles, max_concurrent_profiles=max_concurrent_profiles)

            elif choice == '0':  # Thoát chương trình
                is_run = False
                print("Thoát chương trình.")

            else:
                print("Lựa chọn không hợp lệ. Vui lòng nhập lại.")

if __name__ == '__main__':
    DATA_DIR = Path(__file__).parent/'data.txt'

    PROFILES = []
    with open(DATA_DIR, 'r') as file:
        data = file.readlines()

    for line in data:
        parts = line.strip().split('|')
        profile = parts[0]
        secrets = parts[1].split()
        password = parts[2]
        PROFILES.append({
            'profile': profile,
            'secrets': secrets,
            'password': password
        })

    manager = BrowserManager()
    # nếu có đoạn này thì chạy extension, nếu không thì khôgn chạy extension
    manager.config_extension('meta_wallet.crx')
    # manager.run_multi(PROFILES[:5], max_concurrent_profiles=4)
    manager.run_browser(PROFILES[3])
    # manager.run_terminal(PROFILES)
