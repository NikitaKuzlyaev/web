class MessageText:
    wrong_answer = (
        f"""<i class="bi bi-heartbreak-fill" style='font-size:1rem; color:#f55607'></i> 
        <div style='text-align: center; font-weight: bold;'>★ [WA] Неверный ответ ★</div>"""
        f"Ваш ответ неверен.<br>"
        f"Стоимость задачи понижена.")

    wrong_answer_last_try = (
        f"""<i class="bi bi-heartbreak" style='font-size:1rem; color:#000000'></i> 
        <div style='text-align: center; font-weight: bold;'>★ [WA] Неверный ответ ★</div>"""
        f"Ваш ответ неверен.<br>"
        f"Задача сгорела!")

    correct_answer = (
        f"""<i class="bi bi-check-square-fill" style='font-size:1rem; color:#000000'></i> 
        <div style='text-align: center; font-weight: bold;'>★ [OK] Задача сдана ★</div>"""
        f"Ваш ответ верный!<br>"
        f"Поздравляем!!!🎉")

    @staticmethod
    def points_decrease(points):
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
            <div style='text-align: center; font-weight: bold;'>★ [INFO] Списание ★</div>"""
            f"С баланса списано <b>{points}</b> очков")
        return string

    @staticmethod
    def points_increase(points):
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                <div style='text-align: center; font-weight: bold;'>★ [INFO] Начисление ★</div>"""
            f"Вам начислено <b>{points}</b> очков")
        return string

    @staticmethod
    def problem_add(title, points):
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                    <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Вы купили задачу <b>{title}</b> за <b>{points}</b> очков")
        return string

    @staticmethod
    def problem_remove(title, points):
        string = (
            f"""<i class="bi bi-cone-striped" style='font-size:1rem; color:#cc5500'></i> 
                        <div style='text-align: center; font-weight: bold;'>★ [INFO] Обновление ★</div>"""
            f"Вы потеряли задачу <b>{title}</b> за <b>{points}</b> очков")
        return string