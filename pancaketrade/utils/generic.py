"""Generic utilities."""
import functools
import logging
from typing import Callable

from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def check_chat_id(func: Callable) -> Callable:
    """Compare chat ID with admin's chat ID and refuse access if unauthorized."""

    @functools.wraps(func)
    def wrapper_check_chat_id(this, update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_chat is None:
            logger.debug('No chat ID')
            return
        if context.user_data is None:
            logger.debug('No user data')
            return
        if update.message is None and update.callback_query is None:
            logger.debug('No message')
            return
        if update.message and update.message.text is None and update.callback_query is None:
            logger.debug('No text in message')
            return
        chat_id = update.effective_chat.id
        if chat_id == this.config.secrets.admin_chat_id:
            return func(this, update, context, *args, **kwargs)
        logger.warning(f'Prevented user {chat_id} to interact.')
        context.bot.send_message(
            chat_id=this.config.secrets.admin_chat_id, text=f'Prevented user {chat_id} to interact.'
        )
        if update.message:
            update.message.reply_text('This bot is not public, you are not allowed to use it.')
        elif update.callback_query:
            update.callback_query.answer()

    return wrapper_check_chat_id
