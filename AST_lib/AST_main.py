#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Automation Script for Testing
AST version 1.0.0
Last modified date: 2024/06/18
"""
import re
import traceback
import asyncio
from playwright.async_api import async_playwright, expect
from playwright.async_api import TimeoutError as PwTimeoutError
from utils import get_logger, syncify


class TicketInfo:
    """Dataset for purchase information."""
    # Information from purchase platform.
    order_number = ''
    order_ticket_types = ''
    order_price = ''
    order_seat_area = ''
    order_pickup_ticket = ''
    order_payment_terms = ''

    # Purchase parameters from user input.
    target_url = 'https://kktix.com/'
    target_ticket_types = ''
    target_quantity = 2
    target_seat_area = '特B'.replace(' ', '').replace(',', '|').upper()
    target_price = '2800'
    target_grabbing_date = ''
    target_grabbing_time = ''
    target_pickup_ticket = ''
    target_payment_terms = 'ATM'

    # Account information
    account = 'asdegregdf315987@outlook.com'
    password = 'asfgdeg654d644ds'
    name = 'Superman'
    phone = '66829535845'
    email = account
    id_number = 'A123456789'


class PlatformInfo(TicketInfo):
    """A database for website URL"""
    kktix_home_page_url = 'https://kktix.com/'
    kktix_login_url = 'https://kktix.com/users/sign_in?back_to=%s'


class AST(PlatformInfo):
    """
    Automation Script for Testing:
    A class for using Playwright to run test script automatically via asynchronous.
    """
    def __init__(self):
        self.playwright = None
        self.stop = False
        self.timeout = 45 * 60  # ticket grabbing flow timeout (seconds)
        # basic configuration
        self.logger = get_logger()
        self.curr_url = None

        # auto operation configuration
        self.headless = False
        self.webpage_timeout = 90 * 1000  # 90 seconds
        self.typing_delay = 0.01 * 1000  # 0.01 seconds

        # instantiated object
        # self.browser = None

        # website header configuration
        self.user_agent = \
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        self.lang = 'zh-TW'  # set browser language as Mandarin Chinese
        self.timezone = 'Asia/Taipei'  # set time zone to Taipei
        self.coordinates = {"latitude": 25.034000, "longitude": 121.564555}  # set the coordinates
        self.permissions = ["geolocation"]  # Grant "geolocation" permissions.

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.logger.info(f'====== Trigger playwright service!! ======')
        return self

    async def __aexit__(self, *args, **kwargs):
        if self.stop:
            self.logger.info(f'====== Teardown the Playwright service!! ======\n\n\n')
            await self.playwright.stop()
        else:
            self.logger.info(f'====== Exit the Playwright service!! ======\n')

    def input_logger(self):
        """Log a message to logger."""
        return self.logger()

    async def browser_launch(self) -> iter:
        """Launch Chrome browser and returns the browser instance."""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        self.logger.info(f'- [Playwright service] => Launch browser: Chromium')
        return await self.playwright.chromium.launch(
            args=['--disable-blink-features=AutomationControlled'],
            headless=self.headless,
            slow_mo=0.2*1000)

    async def browser_close(self, _browser: iter) -> None:
        """Closes the browser and all of its pages (if any were opened)."""
        self.logger.info(f'- [Playwright service] => Close browser')
        await _browser.close()
        await self.playwright.stop()

    async def create_windows(self, _browser=None) -> iter:
        """Create a browser context(window), each context can host multiple pages (tabs)."""
        if not _browser:
            _browser = await self.browser_launch()
        self.logger.info(f'- [Playwright service][#index] => Create a new browser window.')
        return await _browser.new_context(
            user_agent=self.user_agent,
            locale=self.lang,  # set the browser language
            timezone_id=self.timezone,  # set the time zone
            geolocation=self.coordinates,  # set geolocation to specific area
            permissions=self.permissions  # Grant website permissions to allow website access
        )

    async def new_page(self, _windows=None) -> iter:
        """
        Add a new browser tab.
        Noted: requires at least a browser context(window) to be created.
        """
        if not _windows:
            _windows = await self.create_windows()
        self.logger.info(f'- [Playwright service][#index] => Open a new page(new tab).')
        return await _windows.new_page()

    async def goto_url(self, _url, _page=None) -> (str, iter):
        """Navigate to a specific website via URL."""
        if not _page:
            _page = await self.new_page()
        self.logger.info(f'- [Playwright service][#index] => Page goto: {_url}')
        await _page.goto(_url, timeout=self.webpage_timeout)
        self.logger.info(f'- [Current URL][#index] =>　{_page.url}')
        _title = await _page.title()
        self.logger.info(f'- [Website title][#index] => {_title}')
        return _title, _page
    
    async def login_auto(self, _page: iter, user_data: dict) -> None:
        """Sign-in automatically via Email account and password."""
        self.logger.debug(f'# Step: login_auto[#index]')
        account = user_data.get('account')
        password = user_data.get('password')
        _, _page = await self.goto_url(self.kktix_login_url, _page)
        self.logger.info(f'- [Simulate user action][#index][typing] => {account}')
        await _page.locator("input#user_login.string.required").type(account, delay=self.typing_delay)
        self.logger.info(f'- [Simulate user action][#index][typing] => {password}')
        await _page.locator("input#user_password.password.required").type(password, delay=self.typing_delay)
        self.logger.info(f'- [Simulate user action][#index][click] => "Sign In" button')
        await _page.locator("input.btn.normal.btn-login").click()
        # await asyncio.sleep(2)  # TODO: remove after completing the develop

    async def init(self) -> iter:
        """Launch the browser and create a context.
        Args:
            No args
        Returns:
            A Context instance of browser
        """
        self.logger.debug(f'# Step[#index]: AST init')
        _browser = await self.browser_launch()
        return await self.create_windows(_browser)

    async def entry_target_web(self, target_url, _page=None):
        """Enter the target url and scroll to button and click next-step button."""
        self.logger.debug(f'# Step[#index]: entry_target_web')
        await self.goto_url(target_url, _page)
        for _ in range(10):
            self.logger.info(f'- [Simulate user action][#index][wheel] => mouse wheel down 800')
            await _page.mouse.wheel(0, 800)
        self.logger.info(f'- [Simulate user action][#index][click] => "下一步" button')
        await _page.get_by_role('link', name="下一步").click()
        return _page.url

    async def fans_question(self, _page=None):
        """Detecting the fans question and auto answering."""
        await _page.locator('.custom-captcha.ng-scope').wait_for(state='attached')
        _ques_popup = _page.locator('.captcha.ng-scope')
        _fans_q = await _ques_popup.locator('.custom-captcha-inner').inner_text()
        self.logger.info(f'[#index] Fans Q&A popup: {_fans_q}')
        await _ques_popup.get_by_role('textbox', name='captcha_answer').fill('')

    async def choose_ticket_type(self, _page=None):
        """
        # step 1: choose ticket type and quantity
        # step 2: click privacy policy (I've read and agreed to Terms of Service and Privacy Policy)
        # step 3: click next step button
        # step 4: bypass reCAPTCHA (might be triggered)
        """
        self.logger.debug(f'# Step[#index]: choose_ticket_type')

        # await asyncio.sleep(.2)  # necessary delay time for loading resource TODO:NIT
        await _page.mouse.wheel(0, 800)
        self.logger.info(f'- [Simulate user action][#index][wheel] => mouse wheel down 800')
        _target_flag = False

        await _page.locator('.ticket-list-wrapper.ng-scope.with-seat').wait_for(state='attached')
        for _row in await _page.locator('.ticket-unit.ng-scope').all():
            self.logger.debug('[#index]=========')
            _ticket_name = await _row.locator('.ticket-name.ng-binding').inner_text()
            _ticket_name = _ticket_name.replace('\n', '')
            self.logger.info(f'- [Data monitoring][#index] => Get ticket-name: {_ticket_name}')
            _ticket_price = await _row.locator('.ticket-price').inner_text()
            self.logger.info(f'- [Data monitoring][#index] => Get ticket-price: {_ticket_price}')

            try:
                await _row.locator('.ticket-seat.ng-binding.ng-scope').wait_for(state='attached', timeout=500)
                _ticket_seat = await _row.locator('.ticket-seat.ng-binding.ng-scope').inner_text()
                self.logger.info(f'- [Data monitoring][#index] => Get ticket-seat: {_ticket_seat}')
            except:
                self.logger.warning(f'- [Data monitoring][#index] => No ticket-seat field')

            if ret := re.search(fr'{self.target_price}', _ticket_price.replace(',', '')):
                self.logger.debug(f'- [Data monitoring][#index] => Found {ret.group()}')
                _target_flag = True
            elif ret := re.search(fr'{self.target_seat_area}', _ticket_name):
                self.logger.debug(f'- [Data monitoring][#index] => Found {ret.group()}')
                _target_flag = True
            else:
                self.logger.debug(f'- [Data monitoring][#index] => Found {ret}')
                _target_flag = False
                # continue  # TODO: Speed up the snap up flow if enable (may raise bug).

            try:
                _ticket_quantity = await _row.locator('.ticket-quantity.ng-scope').inner_text()
                self.logger.info(f'- [Data monitoring][#index] => Get ticket-quantity: {_ticket_quantity}')
                if _target_flag and ('已售完' not in _ticket_quantity):
                    for _ in range(self.target_quantity):
                        self.logger.info(f'- [Simulate user action][#index][click] => "+" plus button')
                        await _row.locator('button.btn-default.plus').click()
                        # await asyncio.sleep(.1)
                    break
                else:
                    self.logger.info(f'- [Data monitoring][#index] => Target sold out!!!')
                    continue
            except Exception as e:
                self.logger.error(f'- [Exception][#index] => Exception: {e}')
            finally:
                _ticket_quantity = await _row.locator('.ticket-quantity.ng-scope').inner_text()
                self.logger.info(
                    f'- [Data monitoring][#index] => Check ticket-quantity: {_ticket_quantity}\n')

        self.logger.info(f'- [Simulate user action][#index][click] => "person agree terms" checkbox')
        await _page.locator('#person_agree_terms').click()
        await _page.get_by_role('button', name='下一步').wait_for(state='attached')
        self.logger.info(f'- [Simulate user action][#index][click] => "下一步" button')
        await _page.get_by_role('button', name='下一步').click()

    async def booking(self, _page=None):
        """This step will be skipped if choosing auto seating in choose_ticket_type process.

        # step 1: click confirm alert (Automatic Seats Allocation Notification)
        # step 2: click confirm
        # step 3: click "Confirm my Purchase" button
        """
        self.logger.debug(f'# Step [#index]: booking')
        pass

    async def fill_out_form(self, _page, _user_data):
        """
        # step 1: fill out "Contact Information", if content is empty
        # step 2: click "Confirm Form"
        """
        self.logger.debug(f'# Step [#index]: fill_out_form')
        _name = _user_data.get('name')
        _email = _user_data.get('email')
        _phone = _user_data.get('phone')

        # Show countdown time for confirming ticket information.
        await _page.locator('.countdown-block.ng-binding.ng-scope').wait_for(state='attached')
        countdown_prompts = await _page.locator('.countdown-block.ng-binding.ng-scope').inner_text()
        self.logger.debug(f'- [Data monitoring][#index] => CountdownPrompts: {countdown_prompts}')
        if countdown_time := re.search(r'([\d-]+:[\d-]+)', countdown_prompts).group():
            self.logger.info(
                f'- [Data monitoring][#index] => Countdown Time for confirmation: {countdown_time}')

        # Capture ticket information
        await _page.locator('.table.data-list.cart-ticket-list.ng-scope').wait_for(state='attached')
        _ticket_info_table = _page.locator('.table.data-list.cart-ticket-list.ng-scope')
        _ticket_types = await _ticket_info_table.locator('.ticket-name.ng-binding').inner_text()
        _ticket_seat = await _ticket_info_table.locator('.seat-info.ng-scope').inner_text()
        _ticket_count = await _ticket_info_table.locator('.align-right.price-count.ng-binding').inner_text()
        _ticket_checkout = await _ticket_info_table.locator('.align-right.price-total.ng-binding').inner_text()

        # Fill out contact info table
        await _page.locator('.contact-info').wait_for(state='attached')
        contact_info_table = _page.locator('.contact-info')
        for contact_list in await contact_info_table.locator('.control-group').all():
            _contact_table_title = await contact_list.locator('.control-label.ng-binding').inner_text()
            _textbox_value = await contact_list.get_by_role('textbox').input_value()
            if '姓名' in _contact_table_title:
                _confirm_name = _textbox_value
                self.logger.info(
                    f'- [Data monitoring][#index] => | {_contact_table_title}:  {_confirm_name}')
                if _confirm_name != _name:
                    self.logger.info(f'- [Simulate user action][#index][fill] => "{_name}" textbox')
                    await contact_list.get_by_role('textbox').fill(_name)
            elif 'Email' in _contact_table_title:
                _confirm_email = _textbox_value
                self.logger.info(
                    f'- [Data monitoring][#index] => | {_contact_table_title}:  {_confirm_email}')
                if _confirm_email != _email:
                    self.logger.info(f'- [Simulate user action][#index][fill] => "{_email}" textbox')
                    await contact_list.get_by_role('textbox').fill(_email)
            elif '手機' in _contact_table_title:
                _confirm_phone = _textbox_value
                self.logger.info(
                    f'- [Data monitoring][#index] => | {_contact_table_title}:  {_confirm_phone}')
                if _confirm_phone != _phone:
                    self.logger.info(f'- [Simulate user action][#index][fill] => "{_phone}" textbox')
                    await contact_list.get_by_role('textbox').fill(_phone)
            else:
                self.logger.error(
                    f'- [Exception][#index] => table_header{_contact_table_title}: {_textbox_value}')

        for checkbox in await _page.locator('.checkbox-inline.ng-binding').all():
            self.logger.info(
                f'- [Simulate user action][#index][click] => "{await checkbox.inner_text()}" checkbox')
            await checkbox.click()
        self.logger.info(f'- [Simulate user action][#index][click] => "確認表單資料" button')
        # # locate the "Confirm Form" button via attributes or css
        # _submit = _page.\
        #     locator('.btn.btn-primary.btn-lg.ng-binding.ng-isolate-scope').get_by_role('link', name='確認表單資料')
        # await _submit.hover()
        # await _submit.wait_for(state='attached')
        # await _submit.click()
        await _page.get_by_text('確認表單資料').wait_for(state='attached')
        await _page.get_by_text('確認表單資料').click()

    async def pay_and_pickup(self, _page, _user_data):
        """
        # stap 1: fill in the ID card number
        # step 2: select ATM payment
        # step 3 : click "Confirm your Order" button
        """
        self.logger.debug(f'# Step[#index]: pay_and_pickup')

        # Show countdown time for payment.
        await _page.locator('.countdown-block.ng-binding.ng-scope').wait_for(state='attached')
        countdown_prompts = await _page.locator('.countdown-block.ng-binding.ng-scope').inner_text()
        self.logger.debug(f'- [Data monitoring][#index] => CountdownPrompts: {countdown_prompts}')
        if countdown_time := re.search(r'[\d-]{4}/[\d-]{2}/[\d-]{2} [\d-]{2}:[\d-]{2}', countdown_prompts).group():
            self.logger.info(f'- [Data monitoring][#index] => Countdown Time for payment: {countdown_time}')

        self.order_number = await _page.locator('.final-order-list-title.ng-scope').inner_text()
        self.logger.info(f'- [Data monitoring][#index] => | Order number: {self.order_number}')

        _ticket_info_form = _page.locator('.cart-ticket-list')
        _ticket_info_css_dict = {
            'ticket_type': '.ticket-name.ng-binding',
            'ticket_seat': '.seat-info.ng-scope',
            'ticket_price': '.align-right.price-count.ng-binding'
        }

        _fmt_line = f'+ {"-" * 15} + {"-" * 15} + {"-" * 15}'
        _header_labels = '| {:^15} | {:^15} | {:^15}'.format(*_ticket_info_css_dict.keys())
        self.logger.info(f'- [Data monitoring][#index] => {_fmt_line}')
        self.logger.info(f'- [Data monitoring][#index] => {_header_labels}')
        self.logger.info(f'- [Data monitoring][#index] => {_fmt_line}')

        for _title, _css in _ticket_info_css_dict.items():
            for _ticket_info in await _ticket_info_form.locator(_css).all():
                _ticket_info_text = await _ticket_info.inner_text()
                _fmt_text = _ticket_info_text.replace('\n', ', ')
                self.logger.debug(f'- [Data monitoring][#index] => | {_title:<15}| {_fmt_text}')

        _total_amount_text = await _page.locator('.highlight').inner_text()
        self.logger.debug(f'- [Data monitoring][#index] => |{"Total_amount":<15}| {_total_amount_text}')

        _pickup_payment_block = _page.locator('.pickup-and-payment-block')

        # Select Pickup ticket method.
        _pickup_block = _pickup_payment_block.locator('.pickup')
        for _radio in await _pickup_block.locator('.control-group.radio').all():
            _pickup_option = await _radio.locator('.radio.ng-binding').inner_text()
            self.logger.debug(f'- [Data monitoring][#index] => Pick up types: {_pickup_option}')
            if '全家' in _pickup_option:
                self.logger.info(
                    f'- [Simulate user action][#index][click] => choose "{_pickup_option}" radio button')
                await _radio.click()
                _id_textbox = _pickup_block.get_by_role('textbox')
                await _id_textbox.wait_for(state='attached')
                id_number = _user_data.get('id_number')
                self.logger.info(f'- [Simulate user action][#index][typing] => {id_number}')
                await _id_textbox.type(id_number, delay=self.typing_delay)
                break

        # Select Payment terms.
        _payment_block = _pickup_payment_block.locator('.payment')
        for _radio in await _payment_block.locator('.control-group.radio').all():
            _payment_option = await _radio.locator('.radio.payment-method-label.ng-binding').inner_text()
            self.logger.debug(f'- [Data monitoring][#index] => Payment types: {_payment_option}')
            if 'ATM' in _payment_option.upper():
                self.logger.info(
                    f'- [Simulate user action][#index][click] => choose "{_payment_option}" radio button')
                await _radio.click()
                break

        # Click the submit button
        try:
            _submit_btn = _page.locator('.btn.btn-primary.btn-lg.ng-binding.ng-isolate-scope').get_by_role('button')
            await _submit_btn.wait_for(state='attached')
            self.logger.info(f'- [Simulate user action][#index][click] => submit button')
            await _submit_btn.click()
        except PwTimeoutError as e:
            self.logger.error(f'- [Exception][#index] => TimeoutError: {e}')

        # await asyncio.sleep(15)


async def run_init(pw_service) -> iter:
    """The initialization for KKTIX ticket grabbing."""
    page = await pw_service.init_control()
    await pw_service.login_auto(page)
    return page


async def run_kktix(pw_service, windows, target_url, user_data):
    """The main process for KKTIX ticket grabbing."""
    _page = await pw_service.new_page(windows)
    await pw_service.login_auto(_page, user_data)
    pw_service.input_logger.info(f'### START[#index]: run_kktix')
    await pw_service.entry_target_web(target_url, _page)
    while True:
        await asyncio.sleep(.01)  # TODO: add random delay time (0.1~0.3)
        pw_service.input_logger.info(f'- [Current URL][#index] =>　{_page.url}')

        if 'kktix.cc/events/' in _page.url:
            await pw_service.entry_target_web(target_url, _page)

        elif re.match(r'https://kktix\.com/events/\w*/registrations/new', _page.url):
            await pw_service.choose_ticket_type(_page)
            # await asyncio.sleep(3)

        elif re.match(r'https://kktix\.com/events/\w*/registrations/[-#\w]*/booking', _page.url):
            await pw_service.booking(_page)
            # await asyncio.sleep(3)

        elif re.match(r'https://kktix\.com/events/\w*/registrations/[-#\w]*(/)$', _page.url):
            _current_stage = await _page.locator('.ng-scope.active').inner_text()
            pw_service.input_logger.info(
                f'- [Data monitoring][#index] => Current stage: {_current_stage}')
            if '填寫表單' in _current_stage:
                await pw_service.fill_out_form(_page, user_data)
                # await asyncio.sleep(3)
            elif '取票繳費' in _current_stage:
                await pw_service.pay_and_pickup(_page, user_data)
                # await asyncio.sleep(3)
                break
            else:
                pw_service.input_logger.error(
                    f'- [Data monitoring][#index] => Exception stage: {_current_stage}')

        else:
            pw_service.input_logger.error(f'- [Data monitoring][#index] => Exception URL: {_page.url}')
            break
    pw_service.input_logger.info(f'### END[#index]: run_kktix')
    await _page.wait_for_timeout(30*1000)


@syncify
async def run_kktix_testflow():
    """The process for testing auto KKTIX ticket-Grabbing."""
    url = 'https://kklivetw.kktix.cc/events/2024kstttsmconcert'
    user_data = {
        'account': 'asdegregdf315987@outlook.com',
        'password': 'asfgdeg654d644ds',
        'name': 'Superman',
        'phone': '66829535845',
        'email': 'asdegregdf315987@outlook.com',
        'id_number': 'A123456789'
    }
    logger = get_logger()
    async with AST() as run:
        browser = await run.browser_launch()
        windows = await run.create_windows(browser)
        _page = await run.new_page(windows)
        await run.login_auto(_page, user_data)
        await run.entry_target_web(url, _page)
        while True:
            logger.info(f'- [Current URL][#index] =>　{_page.url}')

            if 'kktix.cc/events/' in _page.url:
                await run.entry_target_web(url, _page)

            elif re.match(r'https://kktix\.com/events/\w*/registrations/new', _page.url):
                await run.choose_ticket_type(_page)

            elif re.match(r'https://kktix\.com/events/\w*/registrations/[-#\w]*/booking', _page.url):
                await run.booking(_page)

            elif re.match(r'https://kktix\.com/events/\w*/registrations/[-#\w]*(/)$', _page.url):
                _current_stage = await _page.locator('.ng-scope.active').inner_text()
                logger.info(f'- [Data monitoring][#index] => Current stage: {_current_stage}')
                if '填寫表單' in _current_stage:
                    await run.fill_out_form(_page, user_data)
                elif '取票繳費' in _current_stage:
                    await run.pay_and_pickup(_page, user_data)
                    break
                else:
                    logger.error(f'- [Data monitoring][#index] => Exception stage: {_current_stage}')

            else:
                logger.error(f'- [Data monitoring][#index] => Exception URL: {_page.url}')
                break

        await _page.wait_for_timeout(30*1000)


@syncify
async def test_robot():
    # url = 'https://bot.sannysoft.com/'  # crawler bot detection
    url = 'https://antcpt.com/score_detector/'  # reCAPTCHA v3 score testing
    async with AST() as run:
        browser = await run.browser_launch()
        windows = await run.create_windows(browser)
        page = await run.new_page(windows)
        await run.goto_url(url, page)
        await page.pause()


if __name__ == "__main__":
    # asyncio.run(run_kktix_testflow())
    test_robot()

