#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Solution for bypassing CAPTCHA.
Last modified date: 2024/06/11
"""


def bypass_recaptcha_capsolver(url, key, proxy):
    """Bypass reCAPTCHA v2 via capsolver"""
    import capsolver
    capsolver.api_key = "Your Capsolver API Key"
    if proxy:
        solution = capsolver.solve({
            "type": "ReCaptchaV2Task",
            "websiteURL": url,
            "websiteKey": key,
            "proxy": proxy
        })
    else:
        solution = capsolver.solve({
            "type": "ReCaptchaV2TaskProxyless",
            "websiteURL": url,
            "websiteKey": key,
        })
    return solution


if __name__ == "__main__":
    pass
