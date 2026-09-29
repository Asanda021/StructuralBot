"""
StructuralBot - Project Management Handler

Handles:
- Project list
- Create project
- Select project
- Project information
- Delete project
- Project navigation

Engineering calculations are not performed here.
"""

from __future__ import annotations

from typing import Any, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# =========================================================
# TEXTS
# =========================================================

PROJECTS_TEXT = (
    "🏗 <b>پروژه‌های من</b>\n\n"
    "پروژه موردنظر را انتخاب کنید یا یک پروژه جدید بسازید."
)

NO_PROJECTS_TEXT = (
    "🏗 <b>پروژه‌های من</b>\n\n"
    "هنوز پروژه‌ای ثبت نشده است."
)


# =========================================================
# DATABASE COMPATIBILITY
# =========================================================

try:
    from database import (
        get_projects,
        create_project,
        get_project,
        delete_project,
    )
except ImportError:
    get_projects = None
    create_project = None
    get_project = None
    delete_project = None


# =========================================================
# SAFE HELPERS
# =========================================================

def _user_id(update: Update) -> Optional[int]:
    """Return Telegram user ID."""
    if update.effective_user is None:
        return None

    return update.effective_user.id


def _project_value(project: Any, key: str, default: Any = None) -> Any:
    """Read a project field from dict/object safely."""

    if project is None:
        return default

    if isinstance(project, dict):
        return project.get(key, default)

    return getattr(project, key, default)


def _project_id(project: Any) -> Optional[Any]:
    """Extract project ID safely."""

    return _project_value(
        project,
        "id",
        _project_value(project, "project_id"),
    )


def _project_name(project: Any) -> str:
    """Extract project name safely."""

    return str(
        _project_value(
            project,
            "name",
            "پروژه بدون نام",
        )
    )


# =========================================================
# DATABASE OPERATIONS
# =========================================================

def _load_projects(user_id: int) -> list:
    """Load user's projects safely."""

    if get_projects is None:
        return []

    try:
        result = get_projects(user_id)

        if result is None:
            return []

        return list(result)

    except TypeError:
        try:
            result = get_projects(user_id=user_id)

            if result is None:
                return []

            return list(result)

        except Exception:
            return []

    except Exception:
        return []


def _load_project(project_id: Any) -> Any:
    """Load one project safely."""

    if get_project is None:
        return None

    try:
        return get_project(project_id)

    except TypeError:
        try:
            return get_project(project_id=project_id)

        except Exception:
            return None

    except Exception:
        return None


def _create_project(
    user_id: int,
    name: str,
) -> Any:
    """Create a project using the available database API."""

    if create_project is None:
        return None

    try:
        return create_project(
            user_id=user_id,
            name=name,
        )

    except TypeError:
        try:
            return create_project(
                user_id,
                name,
            )

        except Exception:
            return None

    except Exception:
        return None


def _delete_project(project_id: Any) -> bool:
    """Delete a project safely."""

    if delete_project is None:
        return False

    try:
        result = delete_project(project_id)

        if result is None:
            return True

        return bool(result)

    except TypeError:
        try:
            result = delete_project(
                project_id=project_id
            )

            if result is None:
                return True

            return bool(result)

        except Exception:
            return False

    except Exception:
        return False


# =========================================================
# PROJECT LIST KEYBOARD
# =========================================================

def get_projects_keyboard(
    projects: list,
) -> InlineKeyboardMarkup:
    """Build project list keyboard."""

    keyboard = []

    for project in projects:
        project_id = _project_id(project)
        name = _project_name(project)

        if project_id is None:
            continue

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🏗 {name}",
                    callback_data=f"project:open:{project_id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ پروژه جدید",
                callback_data="project:new",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت",
                callback_data="navigation:main",
            )
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# PROJECT MENU KEYBOARD
# =========================================================

def get_project_keyboard(
    project_id: Any,
) -> InlineKeyboardMarkup:
    """Build selected-project menu."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📐 محاسبات سازه",
                    callback_data=f"project:calculations:{project_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🧮 برآورد مصالح",
                    callback_data=f"project:quantities:{project_id}",
                ),
                InlineKeyboardButton(
                    "🔩 میلگرد و Cut List",
                    callback_data=f"project:rebar:{project_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 گزارش‌ها",
                    callback_data=f"project:reports:{project_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ اطلاعات پروژه",
                    callback_data=f"project:info:{project_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑 حذف پروژه",
                    callback_data=f"project:delete:{project_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ پروژه‌های من",
                    callback_data="project:list",
                ),
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="navigation:main",
                ),
            ],
        ]
    )


# =========================================================
# SHOW PROJECTS
# =========================================================

async def show_projects(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Display user's projects."""

    user_id = _user_id(update)

    if user_id is None:
        return

    projects = _load_projects(user_id)

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if projects:
            await query.edit_message_text(
                PROJECTS_TEXT,
                reply_markup=get_projects_keyboard(projects),
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(
                NO_PROJECTS_TEXT,
                reply_markup=get_projects_keyboard([]),
                parse_mode="HTML",
            )

        return

    if update.message:
        if projects:
            await update.message.reply_text(
                PROJECTS_TEXT,
                reply_markup=get_projects_keyboard(projects),
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(
                NO_PROJECTS_TEXT,
                reply_markup=get_projects_keyboard([]),
                parse_mode="HTML",
            )


# =========================================================
# PROJECT CALLBACK
# =========================================================

async def project_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle project-related callbacks."""

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("project:"):
        return

    parts = data.split(":")

    if len(parts) < 2:
        return

    action = parts[1]

    # -----------------------------------------------------
    # PROJECT LIST
    # -----------------------------------------------------

    if action == "list":
        await show_projects(update, context)
        return

    # -----------------------------------------------------
    # NEW PROJECT
    # -----------------------------------------------------

    if action == "new":

        context.user_data["project_creation_active"] = True
        context.user_data["awaiting_project_name"] = True

        await query.edit_message_text(
            "➕ <b>پروژه جدید</b>\n\n"
            "نام پروژه را ارسال کنید.\n\n"
            "مثال:\n"
            "<code>پروژه مسکونی ۵ طبقه</code>",
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # OPEN PROJECT
    # -----------------------------------------------------

    if action == "open":

        if len(parts) < 3:
            return

        project_id = parts[2]

        project = _load_project(project_id)

        if project is None:
            await query.edit_message_text(
                "❌ پروژه پیدا نشد.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ پروژه‌های من",
                                callback_data="project:list",
                            )
                        ]
                    ]
                ),
            )
            return

        context.user_data["current_project_id"] = project_id

        name = _project_name(project)

        await query.edit_message_text(
            f"🏗 <b>{name}</b>\n\n"
            "پروژه انتخاب شد.\n"
            "بخش موردنظر را انتخاب کنید.",
            reply_markup=get_project_keyboard(project_id),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # PROJECT INFORMATION
    # -----------------------------------------------------

    if action == "info":

        if len(parts) < 3:
            return

        project_id = parts[2]

        project = _load_project(project_id)

        if project is None:
            await query.edit_message_text(
                "❌ پروژه پیدا نشد.",
            )
            return

        name = _project_name(project)

        description = _project_value(
            project,
            "description",
            "ثبت نشده",
        )

        structure_type = _project_value(
            project,
            "structure_type",
            "ثبت نشده",
        )

        await query.edit_message_text(
            f"ℹ️ <b>اطلاعات پروژه</b>\n\n"
            f"🏗 نام: {name}\n"
            f"🏢 نوع سازه: {structure_type}\n"
            f"📝 توضیحات: {description}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=f"project:open:{project_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="navigation:main",
                        )
                    ],
                ]
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    if action == "delete":

        if len(parts) < 3:
            return

        project_id = parts[2]

        await query.edit_message_text(
            "⚠️ <b>حذف پروژه</b>\n\n"
            "آیا مطمئن هستید که می‌خواهید این پروژه حذف شود؟",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 بله، حذف شود",
                            callback_data=f"project:delete_confirm:{project_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ انصراف",
                            callback_data=f"project:open:{project_id}",
                        )
                    ],
                ]
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # DELETE CONFIRM
    # -----------------------------------------------------

    if action == "delete_confirm":

        if len(parts) < 3:
            return

        project_id = parts[2]

        deleted = _delete_project(project_id)

        if deleted:
            context.user_data.pop(
                "current_project_id",
                None,
            )

            await query.edit_message_text(
                "✅ پروژه حذف شد.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🏗 پروژه‌های من",
                                callback_data="project:list",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🏠 منوی اصلی",
                                callback_data="navigation:main",
                            )
                        ],
                    ]
                ),
            )

        else:
            await query.edit_message_text(
                "❌ حذف پروژه انجام نشد.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ بازگشت",
                                callback_data=f"project:open:{project_id}",
                            )
                        ]
                    ]
                ),
            )

        return

    # -----------------------------------------------------
    # PROJECT CALCULATIONS
    # -----------------------------------------------------

    if action == "calculations":

        if len(parts) < 3:
            return

        project_id = parts[2]

        context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            "📐 <b>محاسبات سازه</b>\n\n"
            "نوع سازه را انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏢 بتن‌آرمه",
                            callback_data=f"calc:concrete:{project_id}",
                        ),
                        InlineKeyboardButton(
                            "🏗 فولادی",
                            callback_data=f"calc:steel:{project_id}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔀 مرکب",
                            callback_data=f"calc:composite:{project_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=f"project:open:{project_id}",
                        )
                    ],
                ]
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # PROJECT QUANTITIES
    # -----------------------------------------------------

    if action == "quantities":

        if len(parts) < 3:
            return

        project_id = parts[2]

        context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            "🧮 <b>برآورد مصالح</b>\n\n"
            "برآورد مصالح پروژه از اطلاعات اعضای سازه‌ای "
            "محاسبه خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=f"project:open:{project_id}",
                        ),
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="navigation:main",
                        ),
                    ]
                ]
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # PROJECT REBAR
    # -----------------------------------------------------

    if action == "rebar":

        if len(parts) < 3:
            return

        project_id = parts[2]

        context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            "🔩 <b>میلگرد و Cut List</b>\n\n"
            "BBS، Cut List، وزن میلگرد و پرت "
            "برای پروژه در این بخش مدیریت خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=f"project:open:{project_id}",
                        ),
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="navigation:main",
                        ),
                    ]
                ]
            ),
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # PROJECT REPORTS
    # -----------------------------------------------------

    if action == "reports":

        if len(parts) < 3:
            return

        project_id = parts[2]

        context.user_data["current_project_id"] = project_id

        await query.edit_message_text(
            "📊 <b>گزارش‌های پروژه</b>\n\n"
            "گزارش‌های PDF و Excel از داده‌های "
            "محاسباتی پروژه تولید خواهند شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ بازگشت",
                            callback_data=f"project:open:{project_id}",
                        ),
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="navigation:main",
                        ),
                    ]
                ]
            ),
            parse_mode="HTML",
        )

        return


# =========================================================
# PROJECT NAME MESSAGE HANDLER
# =========================================================

async def project_name_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Receive project name during project creation.
    """

    if not context.user_data.get(
        "awaiting_project_name",
        False,
    ):
        return

    if update.message is None:
        return

    name = (update.message.text or "").strip()

    if not name:
        await update.message.reply_text(
            "❌ نام پروژه نمی‌تواند خالی باشد."
        )
        return

    if len(name) > 150:
        await update.message.reply_text(
            "❌ نام پروژه بیش از حد طولانی است.\n"
            "لطفاً نام کوتاه‌تری وارد کنید."
        )
        return

    user_id = _user_id(update)

    if user_id is None:
        return

    project = _create_project(
        user_id=user_id,
        name=name,
    )

    context.user_data["awaiting_project_name"] = False
    context.user_data["project_creation_active"] = False

    if project is None:
        await update.message.reply_text(
            "⚠️ پروژه ثبت نشد.\n\n"
            "اتصال پایگاه داده در حال تکمیل است."
        )
        return

    project_id = _project_id(project)

    if project_id is not None:
        context.user_data["current_project_id"] = project_id

    await update.message.reply_text(
        f"✅ <b>پروژه ساخته شد</b>\n\n"
        f"🏗 نام پروژه:\n{name}\n\n"
        "حالا می‌توانید بخش موردنظر را انتخاب کنید.",
        reply_markup=(
            get_project_keyboard(project_id)
            if project_id is not None
            else InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🏗 پروژه‌های من",
                            callback_data="project:list",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 منوی اصلی",
                            callback_data="navigation:main",
                        )
                    ],
                ]
            )
        ),
        parse_mode="HTML",
    )


# =========================================================
# HANDLER EXPORTS
# =========================================================

__all__ = [
    "show_projects",
    "project_callback",
    "project_name_message",
    "get_projects_keyboard",
    "get_project_keyboard",
]
