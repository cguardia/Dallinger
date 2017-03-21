"""Bots."""

import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dallinger.config import get_config
config = get_config()

logger = logging.getLogger(__file__)


class BotBase(object):

    """A bot."""

    def __init__(self, URL):
        logger.info("Starting up bot with URL: %s." % URL)
        self.URL = URL
        driver_url = config.get('webdriver_url', None)
        driver_type = config.get('webdriver_type', 'phantomjs').lower()
        if driver_url:
            capabilities = {}
            if driver_type == 'firefox':
                capabilities = webdriver.DesiredCapabilities.FIREFOX
            elif driver_type == 'phantomjs':
                capabilities = webdriver.DesiredCapabilities.PHANTOMJS
            else:
                raise ValueError(
                    'Unsupported remote webdriver_type: {}'.format(driver_type))
            self.driver = webdriver.Remote(
                desired_capabilities=capabilities,
                command_executor=driver_url
            )
        elif driver_type == 'phantomjs':
            self.driver = webdriver.PhantomJS()
        elif driver_type == 'firefox':
            self.driver = webdriver.Firefox()
        else:
            raise ValueError(
                'Unsupported webdriver_type: {}'.format(driver_type))
        self.driver.set_window_size(1024, 768)
        logger.info("Started PhantomJs webdriver.")

    def sign_up(self):
        """Accept HIT, give consent and start experiment."""
        print self.URL
        try:
            self.driver.get(self.URL)
            logger.info("Loaded ad page.")
            begin = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'btn-primary')))
            begin.click()
            logger.info("Clicked begin experiment button.")
            self.driver.switch_to_window('Popup')
            self.driver.set_window_size(1024, 768)
            logger.info("Switched to experiment popup.")
            consent = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'consent')))
            consent.click()
            logger.info("Clicked consent button.")
            participate = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'btn-success')))
            participate.click()
            logger.info("Clicked start button.")
            return True
        except TimeoutException:
            logger.error("Error during experiment sign up.")
            return False

    def participate(self):
        """Participate in the experiment."""
        logger.error("Bot class does not define participate method.")
        raise NotImplementedError

    def sign_off(self):
        """Submit questionnaire and finish."""
        try:
            feedback = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'submit-questionnaire')))
            feedback.click()
            logger.info("Clicked submit questionnaire button.")
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.driver.set_window_size(1024, 768)
            logger.info("Switched back to initial window.")
            return True
        except TimeoutException:
            logger.error("Error during experiment sign off.")
            return False

    def run_experiment(self):
        self.sign_up()
        self.participate()
        self.sign_off()