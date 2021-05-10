import sqlite3
import os


def main():

    out_dir = '_output'
    db_location = out_dir + "/ocr-results.db"

    conn = sqlite3.connect(db_location)
    db = conn.cursor()

    entries = db.execute('''SELECT * FROM results ''')

    loadfile = open("_output/loadfile.csv", "w+",encoding="UTF-8")
    loadfile.write("Control Number, File Location, admin\n")

    out_path = os.path.abspath("_output/txt")

    # get input for admin field e.g. yes - 20210316
    while True:
        try:
            user_admin = str(input("text for admin field e.g. yes - 20210316: "))
            break
        except:
            print("please enter correct input")

    for entry in entries:
        ctrl_num = entry[0]      
        loadfile.write("{}, {}\{}.txt,'{}'\n".format(ctrl_num, out_path,ctrl_num, user_admin))
        out_file = "_output/txt/{}.txt".format(entry[0])
        temp = open(out_file, "w+", encoding="UTF-8")
        temp.writelines(entry[1])


if __name__ == "__main__":
    main()