#!/bin/bash

# Название службы
SERVICE_NAME="queue_log"

# Проверяем, существует ли служба
if systemctl list-units --type=service | grep -q "$SERVICE_NAME.service"; then
    echo "Перезапуск службы $SERVICE_NAME..."
    
    # Перезапускаем службу
    systemctl restart "$SERVICE_NAME"

    # Проверяем статус после перезапуска
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "Служба $SERVICE_NAME успешно перезапущена."
    else
        echo "Не удалось перезапустить службу $SERVICE_NAME. Проверьте логи."
    fi
else
    echo "Служба $SERVICE_NAME не найдена. Убедитесь, что она установлена и настроена."
fi
