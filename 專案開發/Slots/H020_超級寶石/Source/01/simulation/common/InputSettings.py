import tkinter as tk
from tkinter import ttk, messagebox, filedialog

global arr_settings
arr_settings = [1, False, False, 0, False]
times = 2


def inputbox():

    def getselect(item):
        print(item, 'selected')

    def unselectall():
        for index, item in enumerate(list1):
            v[index].set('')

    def selectall():
        for index, item in enumerate(list1):
            v[index].set(item)

    def showselect():
        arr_status = [i.get() for i in v if i.get()]
        arr_settings[1] = 'Log Mode' in arr_status
        arr_settings[2] = 'Survival Mode' in arr_status
        arr_settings[4] = 'Force Multiplier' in arr_status
        arr_settings[3] = bet_var.get()
        window.destroy()

    def cmd1():
        arr_settings[0] = times
        showselect()

    def cmd2():
        arr_settings[0] = 3000000
        showselect()

    def cmd3():
        arr_settings[0] = 100000000
        showselect()

    def cmd4():
        arr_settings[0] = 1000000000
        showselect()

    def cmd5():
        arr_settings[0] = 10000000000
        showselect()

    def cmd6():
        arr_settings[0] = 100000000000
        showselect()

    window = tk.Tk()
    window.title('Simulation Settings')
    window.geometry('460x200')

    bet_frame = ttk.LabelFrame(window, text='Bet Options', padding=(10, 5))
    bet_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky='w')
    bet_values = [1, 1.5, 8, 250]
    bet_labels = [f'Bet {value}' for value in bet_values]
    bet_var = tk.IntVar(value=0)
    for idx, label in enumerate(bet_labels):
        ttk.Radiobutton(
            bet_frame,
            text=label,
            variable=bet_var,
            value=idx
        ).grid(row=0, column=idx, padx=5, sticky='w')

    frame1 = tk.Frame(window, pady=10, padx=10)
    frame1.grid(row=1, column=0, sticky='w')

    list1 = ['Log Mode', 'Survival Mode', 'Force Multiplier']
    v = []
    for index, item in enumerate(list1):
        v.append(tk.StringVar())
        ttk.Checkbutton(
            frame1,
            text=item,
            variable=v[-1],
            onvalue=item,
            offvalue='',
            command=lambda item=item: getselect(item)
        ).grid(row=index // 4, column=index % 4, sticky='w')

    ttk.Button(frame1, text=f"{times}次", command=cmd1).grid(row=1, column=0, pady=5)
    ttk.Button(frame1, text='300萬次', command=cmd2).grid(row=1, column=1, pady=5)
    ttk.Button(frame1, text='1億次', command=cmd3).grid(row=1, column=2, pady=5)
    ttk.Button(frame1, text='10億次', command=cmd4).grid(row=1, column=3, pady=5)
    ttk.Button(frame1, text='100億次', command=cmd5).grid(row=2, column=0, pady=5)
    ttk.Button(frame1, text='1000億次', command=cmd6).grid(row=2, column=1, pady=5)

    window.mainloop()
    return arr_settings


if __name__ == '__main__':
    myStatus = inputbox()
    print(myStatus)
