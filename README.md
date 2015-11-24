# [pattr](http://pattr.me)
Truly instant private messaging. No logs. No hassle.

## Install

Clone the repository
```
git clone https://github.com/justinpotts/pattr.git
```

Enter the directory, and create a virtualenv
```
cd pattr
virtualenv venv
```
This creates a sandbox-style environment, where any Python packages you install will not affect your installed packages on your computer, allowing you to work with multiple versions of plugins and modules as they relate to different applications.

Activate your virtualenv
```
source venv/bin/activate
```

Install requirements.txt
```
pip install -r requirements.txt
```

### Payment (Optional)

If you are developing or testing a feature requiring the use of payment follow these extra steps. 

Note: This is not required, and should only be used for those who are explicitly working on payment.

Create an account on [Stripe](https://stripe.com)

Locate your Stripe API testing keys under your account info.

#### Method One (Recommended)

Set an environement variable on your computer, named `PUBLISHABLE_KEY`, with the value of your Stripe API Test Publishable Key.

Repeat the process, naming the second variable `SECRET_KEY`, with the value of your Stripe API Test Private Key.

#### Method Two

In `pattr.py`, locate the `stripe_keys` dictionary. Replace `os.environ.get("PUBLISHABLE_KEY")` and `os.environ.get("SECRET_KEY)` with your respective public and private API keys.

IMPORTANT: Remember to remove these values and replace with the original `os.environ.get` lines.

## Run

To run the server, run `python pattr.py` and visit `localhost:33507` in the browser.

## Contribute

### Issues

If you find an issue on our site, file an issue and let us know. Remember to add steps to reproduce, what should happen, and what is actually happening. Screenshots are always good too.

#### Security testing

If you are interested in testing security, site vulnerablities, or are using a method which has the potential to harm the site or its servers, please use the url `stage.pattr.me`, and notify pattr@pattr.me of your intentions and processes.

On the chance you find a security issue which has the potential of harming our users or site, do not file an issue in our GitHub repository. Instead, please contact pattr@pattr.me using the same format you would when reporting a normal issue (title, steps to reproduce, log files, screenshots).

### Write Code

If you'd like to write code, find an issue that sounds interesting to you, or work on an existing issue in our issues repository. Reach out to a contributor on the project, or send us a message. Be sure to follow [this git workflow](https://gist.github.com/justinpotts/55bf189d9b2af253bf0f).
