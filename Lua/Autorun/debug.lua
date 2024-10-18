local lfs = require("lfs")

function scanDir(directory)
    for file in lfs.dir(directory) do
        if file ~= "." and file ~= ".." then
            local fullPath = directory .. '/' .. file
            local attr = lfs.attributes(fullPath)

            if attr.mode == "directory" then
                scanDir(fullPath) -- Рекурсивно обходим папки
            else
                print("Файл: " .. fullPath) -- Чтение файлов
            end
        end
    end
end

function ShowLoadedPackages()
    print("Загруженные пакеты данных:")
    for package in ContentPackageManager.EnabledPackages.All do
        print("Пакет: " .. package.Name)
        print("Путь до: " .. package.Dir)
        local path = package.Dir
        local file = io.open(path, "r") -- Открываем файл в режиме чтения

        if file then
            local content = file:read("*all") -- Читаем всё содержимое файла
            print(content)                    -- Выводим содержимое файла
            file:close()                      -- Закрываем файл
        else
            print("Не удалось открыть файл: " .. path)
        end

        print("\n")
    end
    print("\n")
end

Game.AddCommand("showloadedpackages", "Вывести список загруженных пакетов", ShowLoadedPackages)
