# -*- coding: utf-8 -*-
import os
import json
import csv
from datetime import datetime, timedelta

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner


DEFAULT_SERVICES = ["حلاقة", "لحية", "حلاقة ولحية"]


def money(v):
    return "{:g}".format(float(v))


class SalonHamzaApp(App):
    def build(self):
        self.title = "صالون حمزة"
        self.load_data()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(8)
        )

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(82)
        )
        header.add_widget(Label(
            text="صالون حمزة",
            font_size=dp(26),
            bold=True
        ))
        header.add_widget(Label(
            text="تسيير المداخيل والمصاريف",
            font_size=dp(13)
        ))
        root.add_widget(header)

        cards = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(120)
        )

        self.total_label = Label()
        self.expense_label = Label()
        self.profit_label = Label()
        self.today_label = Label()

        for widget in (
            self.total_label,
            self.expense_label,
            self.profit_label,
            self.today_label
        ):
            cards.add_widget(widget)

        root.add_widget(cards)

        scroll = ScrollView()
        grid = GridLayout(
            cols=2,
            spacing=dp(6),
            padding=dp(3),
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter("height"))

        buttons = [
            ("1 - تسجيل خدمة", self.add_sale),
            ("2 - البحث في المبيعات", self.search_sales),
            ("3 - إضافة مصروف", self.add_expense),
            ("🧾 المصاريف", self.view_expenses),
            ("4 - مدخول حسب التاريخ", self.daily_income_by_date),
            ("5 - تعديل عملية", self.edit_sale),
            ("6 - حذف مصروف", self.delete_expense),
            ("7 - حذف عملية بيع", self.delete_sale),
            ("8 - التقرير والإحصائيات", self.dashboard_report),
            ("9 - إدارة الخدمات", self.manage_services),
            ("10 - تصفير الحسابات", self.clear_all),
            ("11 - تقرير الخدمات", self.service_report),
            ("12 - تصدير التقرير", self.export_report),
            ("13 - رسم المداخيل", self.income_chart),
            ("14 - كلمة السر", self.set_password),
            ("15 - خروج", self.close_program),
        ]

        for text, command in buttons:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(55),
                font_size=dp(13)
            )
            btn.bind(on_release=lambda _, c=command: c())
            grid.add_widget(btn)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        root.add_widget(Label(
            text="✦ الحفظ تلقائي • بياناتك محفوظة داخل التطبيق ✦",
            size_hint_y=None,
            height=dp(25),
            font_size=dp(11)
        ))

        self.refresh_dashboard()
        return root

    # ---------------- DATA ----------------

    @property
    def data_file(self):
        return os.path.join(
            self.user_data_dir,
            "salon_data.json"
        )

    @property
    def password_file(self):
        return os.path.join(
            self.user_data_dir,
            "salon_password.txt"
        )

    def load_data(self):
        os.makedirs(self.user_data_dir, exist_ok=True)

        try:
            with open(
                self.data_file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        self.sales = data.get("sales", [])
        self.expenses = data.get("expenses", [])
        self.services = data.get(
            "services",
            DEFAULT_SERVICES.copy()
        )

        for sale in self.sales:
            sale.setdefault("service", "حلاقة")
            sale.setdefault("price", 0)
            sale.setdefault("date", "قديم")

        for i, expense in enumerate(self.expenses):
            if isinstance(expense, (int, float)):
                self.expenses[i] = {
                    "name": "مصروف قديم",
                    "amount": expense,
                    "date": "قديم"
                }
            else:
                expense.setdefault("name", "مصروف")
                expense.setdefault("amount", 0)
                expense.setdefault("date", "قديم")

    def save_data(self):
        os.makedirs(self.user_data_dir, exist_ok=True)

        with open(
            self.data_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                {
                    "sales": self.sales,
                    "expenses": self.expenses,
                    "services": self.services
                },
                f,
                ensure_ascii=False,
                indent=4
            )

    # ---------------- UI HELPERS ----------------

    def popup(self, title, content, size=(0.92, 0.80)):
        popup = Popup(
            title=title,
            content=content,
            size_hint=size,
            auto_dismiss=False
        )
        popup.open()
        return popup

    def message(self, title, text):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )
        box.add_widget(Label(
            text=text,
            halign="center"
        ))

        ok = Button(
            text="موافق",
            size_hint_y=None,
            height=dp(48)
        )
        box.add_widget(ok)

        popup = self.popup(
            title,
            box,
            (0.90, 0.42)
        )
        ok.bind(on_release=popup.dismiss)

    def confirm(self, title, text, callback):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )
        box.add_widget(Label(
            text=text,
            halign="center"
        ))

        row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        yes = Button(text="نعم")
        no = Button(text="لا")

        row.add_widget(yes)
        row.add_widget(no)
        box.add_widget(row)

        popup = self.popup(
            title,
            box,
            (0.90, 0.42)
        )

        yes.bind(
            on_release=lambda *_:
            self._confirm_yes(popup, callback)
        )
        no.bind(on_release=popup.dismiss)

    def _confirm_yes(self, popup, callback):
        popup.dismiss()
        callback()

    def form(self, title, fields, callback):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(6)
        )

        inputs = []

        for field in fields:
            label = field[0]
            default = field[1]

            box.add_widget(Label(
                text=label,
                size_hint_y=None,
                height=dp(25)
            ))

            if len(field) > 3 and field[3]:
                widget = Spinner(
                    text=str(default),
                    values=field[3],
                    size_hint_y=None,
                    height=dp(46)
                )
            else:
                widget = TextInput(
                    text=str(default),
                    multiline=False,
                    password=(
                        len(field) > 2 and field[2]
                    ),
                    size_hint_y=None,
                    height=dp(46)
                )

            box.add_widget(widget)
            inputs.append(widget)

        row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(7)
        )

        save = Button(text="حفظ")
        cancel = Button(text="إلغاء")

        row.add_widget(save)
        row.add_widget(cancel)
        box.add_widget(row)

        popup = self.popup(
            title,
            box,
            (0.93, 0.82)
        )

        save.bind(
            on_release=lambda *_:
            callback(inputs, popup)
        )
        cancel.bind(on_release=popup.dismiss)

    def show_lines(self, title, lines):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(7)
        )

        scroll = ScrollView()

        label = Label(
            text="\n".join(lines),
            halign="right",
            valign="top",
            size_hint_y=None
        )
        label.bind(
            texture_size=lambda inst, size:
            setattr(inst, "height", size[1])
        )

        scroll.add_widget(label)
        box.add_widget(scroll)

        close = Button(
            text="إغلاق",
            size_hint_y=None,
            height=dp(48)
        )
        box.add_widget(close)

        popup = self.popup(
            title,
            box,
            (0.95, 0.82)
        )
        close.bind(on_release=popup.dismiss)

    # ---------------- TOTALS ----------------

    def sales_total(self):
        return sum(
            float(s.get("price", 0))
            for s in self.sales
        )

    def expenses_total(self):
        return sum(
            float(e.get("amount", 0))
            for e in self.expenses
        )

    def today_total(self):
        today = datetime.now().strftime("%Y-%m-%d")

        return sum(
            float(s.get("price", 0))
            for s in self.sales
            if s.get("date", "").startswith(today)
        )

    def period_total(self, days):
        now = datetime.now()
        start = now - timedelta(days=days)
        total = 0

        for sale in self.sales:
            try:
                dt = datetime.strptime(
                    sale.get("date", ""),
                    "%Y-%m-%d %H:%M"
                )

                if start <= dt <= now:
                    total += float(
                        sale.get("price", 0)
                    )
            except ValueError:
                pass

        return total

    def month_total(self):
        prefix = datetime.now().strftime("%Y-%m")

        return sum(
            float(s.get("price", 0))
            for s in self.sales
            if s.get("date", "").startswith(prefix)
        )

    def refresh_dashboard(self):
        if not hasattr(self, "total_label"):
            return

        total = self.sales_total()
        expenses = self.expenses_total()
        profit = total - expenses

        self.total_label.text = (
            f"المداخيل\n{money(total)} درهم"
        )

        self.expense_label.text = (
            f"المصاريف\n{money(expenses)} درهم"
        )

        self.profit_label.text = (
            f"الربح الصافي\n{money(profit)} درهم"
        )

        self.today_label.text = (
            f"اليوم\n{money(self.today_total())} درهم\n"
            f"{datetime.now().strftime('%d/%m/%Y')}"
        )

    # ---------------- SALES ----------------

    def add_sale(self):
        service = (
            self.services[0]
            if self.services
            else "حلاقة"
        )

        fields = [
            (
                "الخدمة",
                service,
                False,
                self.services or DEFAULT_SERVICES
            ),
            ("الثمن بالدرهم", "20")
        ]

        def save(inputs, popup):
            service_name = inputs[0].text.strip()

            try:
                price = float(
                    inputs[1].text.strip()
                    .replace(",", ".")
                )

                if not service_name or price < 0:
                    raise ValueError

            except ValueError:
                self.message(
                    "خطأ",
                    "دخل خدمة وثمن صحيح."
                )
                return

            self.sales.append({
                "service": service_name,
                "price": price,
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            })

            self.save_data()
            self.refresh_dashboard()

            popup.dismiss()

            self.message(
                "تم",
                "تم تسجيل الخدمة وحفظها."
            )

        self.form(
            "تسجيل خدمة",
            fields,
            save
        )

    # ---------------- EXPENSES ----------------

    def add_expense(self):
        fields = [
            ("اسم المصروف", ""),
            ("المبلغ بالدرهم", "0")
        ]

        def save(inputs, popup):
            name = inputs[0].text.strip()

            try:
                amount = float(
                    inputs[1].text.strip()
                    .replace(",", ".")
                )

                if not name or amount < 0:
                    raise ValueError

            except ValueError:
                self.message(
                    "خطأ",
                    "دخل اسم المصروف ومبلغ صحيح."
                )
                return

            self.expenses.append({
                "name": name,
                "amount": amount,
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                )
            })

            self.save_data()
            self.refresh_dashboard()

            popup.dismiss()

            self.message(
                "تم",
                f"تم تسجيل المصروف: {name} - "
                f"{money(amount)} درهم."
            )

        self.form(
            "إضافة مصروف",
            fields,
            save
        )

    def view_expenses(self):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(7),
            spacing=dp(6)
        )

        scroll = ScrollView()

        listing = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        listing.bind(
            minimum_height=listing.setter("height")
        )

        scroll.add_widget(listing)
        box.add_widget(scroll)

        close = Button(
            text="إغلاق",
            size_hint_y=None,
            height=dp(48)
        )
        box.add_widget(close)

        popup = self.popup(
            "🧾 لائحة المصاريف",
            box,
            (0.97, 0.90)
        )

        def refresh():
            listing.clear_widgets()
            total = 0

            for index, expense in enumerate(
                self.expenses
            ):
                amount = float(
                    expense.get("amount", 0)
                )

                total += amount

                row = BoxLayout(
                    size_hint_y=None,
                    height=dp(65),
                    spacing=dp(4)
                )

                text = (
                    f"{expense.get('name', 'مصروف')}\n"
                    f"{money(amount)} درهم | "
                    f"{expense.get('date', 'قديم')}"
                )

                row.add_widget(
                    Label(
                        text=text,
                        font_size=dp(11)
                    )
                )

                edit = Button(
                    text="تعديل",
                    size_hint_x=None,
                    width=dp(75)
                )

                delete = Button(
                    text="حذف",
                    size_hint_x=None,
                    width=dp(70)
                )

                edit.bind(
                    on_release=lambda _, idx=index:
                    self.edit_expense(
                        idx,
                        refresh
                    )
                )

                delete.bind(
                    on_release=lambda _, idx=index:
                    self.remove_expense(
                        idx,
                        refresh
                    )
                )

                row.add_widget(edit)
                row.add_widget(delete)

                listing.add_widget(row)

            listing.add_widget(
                Label(
                    text=(
                        f"مجموع المصاريف: "
                        f"{money(total)} درهم"
                    ),
                    size_hint_y=None,
                    height=dp(45),
                    bold=True
                )
            )

        close.bind(on_release=popup.dismiss)

        refresh()

    def edit_expense(self, index, refresh=None):
        expense = self.expenses[index]

        fields = [
            (
                "اسم المصروف",
                expense.get("name", "مصروف")
            ),
            (
                "المبلغ بالدرهم",
                money(expense.get("amount", 0))
            )
        ]

        def save(inputs, popup):
            name = inputs[0].text.strip()

            try:
                amount = float(
                    inputs[1].text.strip()
                    .replace(",", ".")
                )

                if not name or amount < 0:
                    raise ValueError

            except ValueError:
                self.message(
                    "خطأ",
                    "تأكد من الاسم والمبلغ."
                )
                return

            self.expenses[index]["name"] = name
            self.expenses[index]["amount"] = amount

            self.save_data()
            self.refresh_dashboard()

            popup.dismiss()

            if refresh:
                refresh()

        self.form(
            "تعديل المصروف",
            fields,
            save
        )

    def remove_expense(self, index, refresh=None):
        expense = self.expenses[index]

        def yes():
            self.expenses.pop(index)
            self.save_data()
            self.refresh_dashboard()

            if refresh:
                refresh()

        self.confirm(
            "تأكيد الحذف",
            f"حذف {expense.get('name', 'مصروف')} - "
            f"{money(expense.get('amount', 0))} درهم؟",
            yes
        )

    def delete_expense(self):
        if not self.expenses:
            self.message(
                "المصاريف",
                "ما كاين حتى مصروف."
            )
            return

        self.view_expenses()

    # ---------------- DELETE / EDIT SALES ----------------

    def delete_sale(self):
        if not self.sales:
            self.message(
                "المبيعات",
                "ما كاين حتى عملية بيع."
            )
            return

        box = BoxLayout(
            orientation="vertical",
            padding=dp(7)
        )

        scroll = ScrollView()

        listing = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        listing.bind(
            minimum_height=listing.setter("height")
        )

        scroll.add_widget(listing)
        box.add_widget(scroll)

        close = Button(
            text="إغلاق",
            size_hint_y=None,
            height=dp(48)
        )

        box.add_widget(close)

        popup = self.popup(
            "حذف عملية بيع",
            box,
            (0.96, 0.90)
        )

        for index, sale in enumerate(self.sales):
            button = Button(
                text=(
                    f"{index + 1} - "
                    f"{sale.get('service', '')} - "
                    f"{money(sale.get('price', 0))} درهم\n"
                    f"{sale.get('date', 'قديم')}"
                ),
                size_hint_y=None,
                height=dp(63)
            )

            button.bind(
                on_release=lambda _, idx=index:
                self.confirm_delete_sale(
                    idx,
                    popup
                )
            )

            listing.add_widget(button)

        close.bind(on_release=popup.dismiss)

    def confirm_delete_sale(self, index, parent):
        sale = self.sales[index]

        def yes():
            self.sales.pop(index)
            self.save_data()
            self.refresh_dashboard()
            parent.dismiss()

        self.confirm(
            "تأكيد",
            f"حذف هاد العملية؟\n"
            f"{sale.get('service', '')} - "
            f"{money(sale.get('price', 0))} درهم",
            yes
        )

    def edit_sale(self):
        if not self.sales:
            self.message(
                "تعديل",
                "ما كاين حتى عملية بيع."
            )
            return

        box = BoxLayout(
            orientation="vertical",
            padding=dp(7)
        )

        scroll = ScrollView()

        listing = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        listing.bind(
            minimum_height=listing.setter("height")
        )

        scroll.add_widget(listing)
        box.add_widget(scroll)

        close = Button(
            text="إغلاق",
            size_hint_y=None,
            height=dp(48)
        )

        box.add_widget(close)

        popup = self.popup(
            "اختار العملية للتعديل",
            box,
            (0.96, 0.90)
        )

        for index, sale in enumerate(self.sales):
            button = Button(
                text=(
                    f"{index + 1} - "
                    f"{sale.get('service', '')} - "
                    f"{money(sale.get('price', 0))} درهم\n"
                    f"{sale.get('date', 'قديم')}"
                ),
                size_hint_y=None,
                height=dp(65)
            )

            button.bind(
                on_release=lambda _, idx=index:
                self.open_edit_sale(idx, popup)
            )

            listing.add_widget(button)

        close.bind(on_release=popup.dismiss)

    def open_edit_sale(self, index, parent):
        parent.dismiss()

        sale = self.sales[index]

        try:
            old = datetime.strptime(
                sale.get("date", ""),
                "%Y-%m-%d %H:%M"
            )

            date_value = old.strftime("%d/%m/%Y")
            time_value = old.strftime("%H:%M")

        except ValueError:
            date_value = datetime.now().strftime(
                "%d/%m/%Y"
            )
            time_value = "12:00"

        fields = [
            (
                "الخدمة",
                sale.get("service", "")
            ),
            (
                "المبلغ",
                money(sale.get("price", 0))
            ),
            (
                "التاريخ (يوم/شهر/سنة)",
                date_value
            ),
            (
                "الساعة",
                time_value
            )
        ]

        def save(inputs, popup):
            try:
                service = inputs[0].text.strip()

                price = float(
                    inputs[1].text.strip()
                    .replace(",", ".")
                )

                dt = datetime.strptime(
                    inputs[2].text.strip()
                    + " "
                    + inputs[3].text.strip(),
                    "%d/%m/%Y %H:%M"
                )

                if not service or price < 0:
                    raise ValueError

            except ValueError:
                self.message(
                    "خطأ",
                    "تأكد من الخدمة والمبلغ "
                    "والتاريخ والساعة."
                )
                return

            self.sales[index] = {
                "service": service,
                "price": price,
                "date": dt.strftime(
                    "%Y-%m-%d %H:%M"
                )
            }

            self.save_data()
            self.refresh_dashboard()

            popup.dismiss()

            self.message(
                "تم",
                "تعدلت العملية بنجاح."
            )

        self.form(
            "تعديل العملية",
            fields,
            save
        )

    # ---------------- SEARCH ----------------

    def search_sales(self):
        fields = [
            (
                "بحث: تاريخ أو خدمة أو ثمن",
                ""
            )
        ]

        def search(inputs, popup):
            query = inputs[0].text.strip().lower()

            lines = []

            for index, sale in enumerate(self.sales):
                date = sale.get("date", "")

                searchable = (
                    f"{sale.get('service', '')} "
                    f"{sale.get('price', '')} "
                    f"{date} "
                    f"{date[:10].replace('-', '/')}"
                )

                if query in searchable.lower():
                    lines.append(
                        f"{index + 1} - "
                        f"{sale.get('service', '')} - "
                        f"{money(sale.get('price', 0))} درهم - "
                        f"{date}"
                    )

            popup.dismiss()

            self.show_lines(
                "نتائج البحث",
                lines or ["ما لقيت حتى نتيجة."]
            )

        self.form(
            "البحث في المبيعات",
            fields,
            search
        )

    # ---------------- DATE REPORT ----------------

    def daily_income_by_date(self):
        fields = [
            (
                "التاريخ (مثال 16/08/2026)",
                datetime.now().strftime("%d/%m/%Y")
            )
        ]

        def search(inputs, popup):
            try:
                selected = datetime.strptime(
                    inputs[0].text.strip(),
                    "%d/%m/%Y"
                ).strftime("%Y-%m-%d")

            except ValueError:
                self.message(
                    "خطأ",
                    "دخل التاريخ بالشكل: 16/08/2026"
                )
                return

            lines = []
            total = 0
            count = 0

            for sale in self.sales:
                if sale.get(
                    "date",
                    ""
                ).startswith(selected):

                    count += 1

                    total += float(
                        sale.get("price", 0)
                    )

                    lines.append(
                        f"{count} - "
                        f"{sale.get('service', '')} - "
                        f"{money(sale.get('price', 0))} درهم - "
                        f"{sale.get('date', '')}"
                    )

            popup.dismiss()

            header = (
                f"مجموع المدخول: "
                f"{money(total)} درهم | "
                f"عدد العمليات: {count}"
            )

            self.show_lines(
                "مدخول حسب التاريخ",
                [header] + (
                    lines or
                    ["ما كاين حتى عملية فهاد النهار."]
                )
            )

        self.form(
            "مدخول حسب التاريخ",
            fields,
            search
        )

    # ---------------- REPORTS ----------------

    def dashboard_report(self):
        total = self.sales_total()
        expenses = self.expenses_total()

        self.message(
            "التقرير",
            f"مداخيل اليوم: "
            f"{money(self.today_total())} درهم\n"
            f"مداخيل آخر 7 أيام: "
            f"{money(self.period_total(7))} درهم\n"
            f"مداخيل الشهر الحالي: "
            f"{money(self.month_total())} درهم\n\n"
            f"مجموع المداخيل: "
            f"{money(total)} درهم\n"
            f"مجموع المصاريف: "
            f"{money(expenses)} درهم\n"
            f"الربح الصافي: "
            f"{money(total - expenses)} درهم\n"
            f"عدد الخدمات: {len(self.sales)}"
        )

    def service_report(self):
        counts = {}
        totals = {}

        for sale in self.sales:
            name = sale.get("service", "")

            counts[name] = (
                counts.get(name, 0) + 1
            )

            totals[name] = (
                totals.get(name, 0)
                + float(sale.get("price", 0))
            )

        if not counts:
            self.message(
                "تقرير الخدمات",
                "ما كاين حتى مبيعات."
            )
            return

        lines = [
            "تقرير الخدمات",
            ""
        ]

        for name in sorted(
            counts,
            key=counts.get,
            reverse=True
        ):
            lines.append(
                f"{name}: "
                f"{counts[name]} خدمات - "
                f"{money(totals[name])} درهم"
            )

        lines.extend([
            "",
            "الأكثر طلباً: "
            + max(counts, key=counts.get)
        ])

        self.show_lines(
            "تقرير الخدمات",
            lines
        )

    def income_chart(self):
        daily = {}

        for sale in self.sales:
            day = sale.get("date", "")[:10]

            if len(day) == 10:
                daily[day] = (
                    daily.get(day, 0)
                    + float(sale.get("price", 0))
                )

        if not daily:
            self.message(
                "الرسم البياني",
                "ما كاين حتى مبيعات."
            )
            return

        lines = [
            "رسم المداخيل - آخر 14 يوم",
            ""
        ]

        for day in sorted(daily)[-14:]:
            amount = daily[day]

            bars = "█" * min(
                35,
                max(1, int(amount / 10))
            )

            lines.append(
                f"{day} | "
                f"{bars} "
                f"{money(amount)} DH"
            )

        self.show_lines(
            "رسم المداخيل",
            lines
        )

    # ---------------- SERVICES ----------------

    def manage_services(self):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(7),
            spacing=dp(6)
        )

        scroll = ScrollView()

        listing = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )

        listing.bind(
            minimum_height=listing.setter("height")
        )

        scroll.add_widget(listing)
        box.add_widget(scroll)

        row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(6)
        )

        add = Button(text="إضافة")
        close = Button(text="إغلاق")

        row.add_widget(add)
        row.add_widget(close)

        box.add_widget(row)

        popup = self.popup(
            "إدارة الخدمات",
            box,
            (0.94, 0.84)
        )

        def refresh():
            listing.clear_widgets()

            for index, service in enumerate(
                self.services
            ):
                r = BoxLayout(
                    size_hint_y=None,
                    height=dp(52),
                    spacing=dp(4)
                )

                r.add_widget(
                    Label(text=service)
                )

                delete = Button(
                    text="حذف",
                    size_hint_x=None,
                    width=dp(70)
                )

                delete.bind(
                    on_release=lambda _, idx=index:
                    self.delete_service(
                        idx,
                        refresh
                    )
                )

                r.add_widget(delete)
                listing.add_widget(r)

        add.bind(
            on_release=lambda *_:
            self.add_service(refresh)
        )

        close.bind(
            on_release=popup.dismiss
        )

        refresh()

    def add_service(self, refresh=None):
        fields = [
            ("اسم الخدمة", "")
        ]

        def save(inputs, popup):
            name = inputs[0].text.strip()

            if not name:
                return

            if name in self.services:
                self.message(
                    "الخدمات",
                    "هاد الخدمة موجودة من قبل."
                )
                return

            self.services.append(name)
            self.save_data()

            popup.dismiss()

            if refresh:
                refresh()

        self.form(
            "إضافة خدمة",
            fields,
            save
        )

    def delete_service(self, index, refresh=None):
        name = self.services[index]

        def yes():
            self.services.pop(index)
            self.save_data()

            if refresh:
                refresh()

        self.confirm(
            "تأكيد",
            f"حذف {name} ؟",
            yes
        )

    # ---------------- PASSWORD ----------------

    def set_password(self):
        fields = [
            ("كلمة السر الجديدة", "", True),
            ("عاود كلمة السر", "", True)
        ]

        def save(inputs, popup):
            first = inputs[0].text
            second = inputs[1].text

            if first != second:
                self.message(
                    "خطأ",
                    "كلمتا السر مختلفتان."
                )
                return

            if not first:
                if os.path.exists(
                    self.password_file
                ):
                    os.remove(
                        self.password_file
                    )
            else:
                with open(
                    self.password_file,
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(first)

            popup.dismiss()

            self.message(
                "تم",
                "تم حفظ كلمة السر."
            )

        self.form(
            "كلمة السر",
            fields,
            save
        )

    # ---------------- OTHER ----------------

    def clear_all(self):
        def yes():
            self.sales.clear()
            self.expenses.clear()

            self.save_data()
            self.refresh_dashboard()

            self.message(
                "تم",
                "رجع الحساب للصفر."
            )

        self.confirm(
            "تأكيد التصفير",
            "غادي يتم حذف جميع المبيعات والمصاريف.\n"
            "واش متأكد؟",
            yes
        )

    def export_report(self):
        path = os.path.join(
            self.user_data_dir,
            "salon_report.csv"
        )

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:
            writer = csv.writer(f)

            writer.writerow([
                "الخدمة",
                "المبلغ",
                "التاريخ"
            ])

            for sale in self.sales:
                writer.writerow([
                    sale.get("service", ""),
                    sale.get("price", 0),
                    sale.get("date", "قديم")
                ])

            writer.writerow([])

            writer.writerow([
                "اسم المصروف",
                "المبلغ",
                "التاريخ"
            ])

            for expense in self.expenses:
                writer.writerow([
                    expense.get(
                        "name",
                        "مصروف"
                    ),
                    expense.get(
                        "amount",
                        0
                    ),
                    expense.get(
                        "date",
                        "قديم"
                    )
                ])

        self.message(
            "التقرير",
            "تم حفظ التقرير داخل بيانات التطبيق:\n"
            "salon_report.csv"
        )

    def close_program(self):
        self.save_data()
        self.stop()


if __name__ == "__main__":
    SalonHamzaApp().run()
