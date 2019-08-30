#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
#
# THIS EXAMPLE HAS BEEN UPDATED TO WORK WITH THE BETA VERSION 12 OF PYTHON-TELEGRAM-BOT.
# If you're still using version 11.1.0, please see the examples at
# https://github.com/python-telegram-bot/python-telegram-bot/tree/v11.1.0/examples

"""
Basic example for a bot that can receive payment from user.
"""

import logging

from telegram import (LabeledPrice, ShippingOption)
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, PreCheckoutQueryHandler, ShippingQueryHandler)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start_callback(update, context):
    msg = "Use /shipping to get an invoice for shipping-payment, "
    msg += "or /noshipping for an invoice without shipping."
    update.message.reply_text(msg)


def start_with_shipping_callback(update, context):
    chat_id = update.message.chat_id
    title = "Payment Example"
    description = "Payment Example using python-telegram-bot"
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    provider_token = "381764678:TEST:11057"
    start_parameter = "test-payment"
    currency = "RUB"
    # price in dollars
    price = 1
    # price * 100 so as to include 2 d.p.
    # check https://core.telegram.org/bots/payments#supported-currencies for more details
    prices = [LabeledPrice("Test", 1000)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    context.bot.send_invoice(chat_id, title, description, payload,
                             provider_token, start_parameter, currency, prices,
                             need_name=True, need_phone_number=True,
                             need_email=True, need_shipping_address=True, is_flexible=True)


def start_without_shipping_callback(update, context):
    chat_id = update.message.chat_id
    title = "Payment Example"
    description = "Payment Example using python-telegram-bot"
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    provider_token = "381764678:TEST:11057"
    start_parameter = "test-payment"
    currency = "RUB"
    price = 1
    prices = [LabeledPrice("Test", 1000)]

    context.bot.send_invoice(chat_id, title, description, payload,
                             provider_token, start_parameter, currency, prices)


def shipping_callback(update, context):
    query = update.shipping_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Something went wrong...")
        return
    else:
        options = list()
        options.append(ShippingOption('1', 'Shipping Option A', [LabeledPrice('A', 100)]))
        price_list = [LabeledPrice('B1', 150), LabeledPrice('B2', 200)]
        options.append(ShippingOption('2', 'Shipping Option B', price_list))
        query.answer(ok=True, shipping_options=options)


def precheckout_callback(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update, context):
    update.message.reply_text("Thank you for your payment!")


def main():
    updater = Updater("664262900:AAFsFJQYE0g-kUOiG_U1_6F3n5Mt4EFY4bs", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_callback))
    dp.add_handler(CommandHandler("shipping", start_with_shipping_callback))
    dp.add_handler(CommandHandler("noshipping", start_without_shipping_callback))
    dp.add_handler(ShippingQueryHandler(shipping_callback))
    dp.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
