<?php
if (!isset($_GET['phone'])) {
    echo "false";
    exit;
}

$phone = $_GET['phone'];
$db_path = '/var/lib/asterisk/astdb.sqlite3';  // Путь к файлу базы данных AstDB

// Проверяем, существует ли файл базы данных
if (!file_exists($db_path)) {
    echo "false";
    exit;
}

try {
    // Подключение к базе данных SQLite
    $db = new PDO("sqlite:$db_path");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Проверка наличия конкретного ключа /fop2state/PJSIP/<номер>
    $specificKey = "/fop2state/PJSIP/$phone";
    $checkQuery = $db->prepare("SELECT * FROM astdb WHERE key = ?");
    $checkQuery->execute([$specificKey]);

    // Вывод результата: true, если ключ существует, иначе false
    if ($checkQuery->fetch()) {
        echo "true";
    } else {
        echo "false";
    }

} catch (PDOException $e) {
    echo "false";
}
