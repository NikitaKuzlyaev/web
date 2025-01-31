from django.utils.timezone import now
import pytz

# Получение текущего времени в UTC+7
timezone_utc7 = pytz.timezone('Asia/Bangkok')  # UTC+7


class MessageText:
    @staticmethod
    def wrong_answer():
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-heartbreak-fill" style='font-size:1rem; color:#f55607'></i> 
            <div style='text-align: center; font-weight: bold;'>★ [WA] Неверный ответ ★</div>"""
            f"Ваш ответ неверен.<br>"
            f"Награда задачи понижена."
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def wrong_answer_last_try():
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-heartbreak" style='font-size:1rem; color:#000000'></i> 
            <div style='text-align: center; font-weight: bold;'>★ [WA] Неверный ответ ★</div>"""
            f"Ваш ответ неверен.<br>"
            f"Задача сгорела!"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def correct_answer():
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-check-square-fill" style='font-size:1rem; color:#000000'></i> 
            <div style='text-align: center; font-weight: bold;'>★ [OK] Задача сдана ★</div>"""
            f"Ваш ответ верный!<br>"
            f"Поздравляем!!!🎉"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def points_decrease(points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
            <div style='text-align: center; font-weight: bold;'>★ [INFO] Списание ★</div>"""
            f"С баланса списано <b>{points}</b> очков"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def points_increase(points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                <div style='text-align: center; font-weight: bold;'>★ [INFO] Начисление ★</div>"""
            f"Вам начислено <b>{points}</b> очков за задачу"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def points_increase_with_combo_points(points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)

        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                        <div style='text-align: center; font-weight: bold;'>★ [INFO] Начисление ★</div>"""
            f"Вам начислено <b>{points}</b> очков (за бонус комбо)"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def problem_add(title, points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                    <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Вы купили задачу <b>{title}</b> за <b>{points}</b> очков"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def problem_remove(title, points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                        <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Вы потеряли задачу <b>{title}</b> за <b>{points}</b> очков"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def combo_points_increase(points):
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                            <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Вам начислено <b>{points}</b> комбо-баллов"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string

    @staticmethod
    def combo_points_remove():
        current_time_utc7 = now().astimezone(timezone_utc7).replace(tzinfo=None)
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                                <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Все ваши комбо-баллы сгорели"
            f"""<div style='text-align: center; font-size: 0.8rem;'>{current_time_utc7}</div>""")
        return string
