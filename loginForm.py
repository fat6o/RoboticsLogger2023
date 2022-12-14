import os
from tkinter import *
from tkinter.ttk import Style
from tkinter import messagebox
import pandas as pd
from datetime import datetime
from github import Github
from github.GithubException import UnknownObjectException, GithubException
from dotenv import load_dotenv

# TODO: Make the csv file change every year so future years can use this program
# TODO: make everyone's current hours in the main menu aligned to the right
# TODO: Make message confirmation boxes colored
# TODO: Add colored text to messageboxes and main menu
# TODO: Make the search string display show (partial match)
# TODO: Comment this code
# TODO: Organize this code into multiple files and stuff
# TODO: Make the system for giving people custom name modifiers easy to use and edit



# Default hours for someone that forgets to sign out
DEFAULT_HOURS = 0.25

# Github stuff
load_dotenv()
user = os.environ.get("GITHUB_USER")
password = os.environ.get("ACCESS_TOKEN")
g = Github(password)
build = os.environ.get("build")
filename = "log.csv"
# if build == "RoboticsLog":
#     print("\u001b[36mServer repo: RoboticsLog\u001b[0m")
# elif build == "RoboticsLogDevelopment":
#     print("\u001b[33mServer repo: RoboticsLogDevelopment\u001b[0m")
# else:
#     raise Exception(
#         f"Invalid build: {build}\nPlease set the BUILD= in the .env file to either RoboticsLog or RoboticsLogDevelopment.")


def gitDownload(filepath):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    day = now.weekday()
    day_of_the_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    commit_message = "Updated " + date + " (" + day_of_the_week[day] + ")"


    try:
        repo = g.get_user().get_repo(build)  # repo name
    except UnknownObjectException:
        account = g.get_user()
        repo = account.create_repo(build)
        print(f"\u001b[31mRepo has been created\u001b[0m")
        new_csv = pd.DataFrame(columns=['Name'])
        with open("members.txt", "r") as f:
            members = f.readlines()
        for member in members:
            member = member.replace("\n", "")
            new_csv = new_csv.append({'Name': member}, ignore_index=True)
            new_csv['Hours'] = "0:00:00"
        new_csv.to_csv("log.csv", index=False)
        git_prefix = ''
        with open(filename, 'r') as file:
            content = file.read()
        git_file = git_prefix + filename
        repo.create_file(git_file, commit_message, content, branch="main")
        print(f"\u001b[32m{git_file} created\u001b[0m")



    all_files = []
    try:
        contents = repo.get_contents("")
    except GithubException:
        print("Some Exception, probably a 404 where repo is empty")
        new_csv = pd.DataFrame(columns=['Name', 'Hours'])
        with open("members.txt", "r") as f:
            members = f.readlines()
        for member in members:
            member = member.replace("\n", "")
            new_csv = new_csv.append({'Name': member}, ignore_index=True)
            new_csv['Hours'] = "0:00:00"
        new_csv.to_csv(filepath, index=False)
        git_prefix = ''
        git_file = git_prefix + filename
        with open(filename, 'r') as file:
            content = file.read()
        repo.create_file(git_file, commit_message, content, branch="main")
        print(f"\u001b[32m{git_file} created\u001b[0m")
        return

    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="', '').replace('")', ''))

    # Download from github
    git_prefix = ''
    git_file = git_prefix + filename
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        with open(filepath, "wb") as f:
            f.write(contents.decoded_content)
    else:
        print(f"\u001b[31m{git_file} not found\u001b[0m")


def gitUpload():
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    day = now.weekday()
    day_of_the_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    commit_message = "Updated " + date + " (" + day_of_the_week[day] + ")"

    repo = g.get_user().get_repo(build)  # repo name

    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="', '').replace('")', ''))

    with open(filename, 'r') as file:
        content = file.read()

    # Upload to github
    git_prefix = ''
    git_file = git_prefix + filename
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(contents.path, commit_message, content, contents.sha, branch="main")
        print(f"\u001b[32m{git_file} updated\u001b[0m")
    else:
        repo.create_file(git_file, commit_message, content, branch="main")
        print(f"\u001b[32m{git_file} created\u001b[0m")

    return commit_message


# File import
gitDownload(filename)
df = pd.read_csv(filename)
df.to_csv(filename, index=False)

# Soft-banned means that the user has logged in once that day, and they cannot have another session where they fail
# to log out and receive an extra hour, but they can still log in and get more hours normally.
#
# Hard-banned means that the user has failed to log out in the first session and cannot sign in again.
soft_banned = []
hard_banned = []


def sync(dataframe):
    gitDownload("OG.csv")
    ogdf = pd.read_csv("OG.csv")
    ogdf.to_csv("OG.csv", index=False)
    ognow = datetime.now()
    ogcurrent_date = ognow.strftime("%Y-%m-%d")
    if ogcurrent_date in ogdf.columns:
        for name in ogdf["Name"]:
            if str(ogdf.loc[ogdf.index[ogdf["Name"] == name].tolist()[0], ogcurrent_date]) != "nan":
                if ("Not Signed Out" in str(ogdf.loc[ogdf.index[ogdf['Name'] == name].tolist()[0], ogcurrent_date])):
                    hard_banned.append(name)
                    print(f"\u001b[31m{name} is hard-banned\u001b[0m")
                else:
                    soft_banned.append(name)
                    print(f"\u001b[31m{name} is soft-banned\u001b[0m")
                print(
                    f"\u001b[33m{name}: {str(dataframe.loc[dataframe.index[dataframe['Name'] == name].tolist()[0], ogcurrent_date])} -> {str(ogdf.loc[ogdf.index[ogdf['Name'] == name].tolist()[0], ogcurrent_date])}\u001b[0m")
                dataframe.loc[dataframe.index[dataframe["Name"] == name].tolist()[0], ogcurrent_date] = ogdf.loc[
                    ogdf.index[ogdf["Name"] == name].tolist()[0], ogcurrent_date]

    try:
        os.remove("OG.csv")
        print("\u001b[32mOG.csv removed successfully\u001b[0m")
    except OSError as error:
        print(error)
        print("\u001b[31mOG.csv can not be removed\u001b[0m")


sync(df)

# Create cache to store all people that have signed in and not signed out
signed_in = []

# Reset today's date and create column if needed
now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
if current_date not in df.columns:
    df[current_date] = ""


# Time manipulation functions
def time_difference(start_time, end_time):
    og = start_time.split(":")
    new = end_time.split(":")
    return (int((new[0])) - int(og[0])) * 3600 + (int(new[1]) - int(og[1])) * 60 + (int(new[2]) - int(og[2]))


def seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 3600) % 60
    return str(hours) + ":" + str(minutes) + ":" + str(seconds)


def time_to_seconds(time):
    hours = int(time.split(":")[0])
    minutes = int(time.split(":")[1])
    seconds = int(time.split(":")[2])
    return hours * 3600 + minutes * 60 + seconds


# Converts a list into a string
def list_to_string(list):
    string = ""
    for i in list:
        string += i + ", "
    return string[:-2]


# root window

# TODO: Add the robotics icon
root = Tk()
root.title("ShivamBad Sign-In Form")


# Closing
def on_closing(df):
    # TODO: open new window allowing user to input number of hours for people that haven't signed out
    if len(signed_in) > 0:
        if messagebox.askokcancel("Quit",
                                  f"Do you want to quit? The following people have not signed out and will be set to a default of f{DEFAULT_HOURS} hour(s): {list_to_string(signed_in)}"):
            sync(df)
            for name in signed_in:
                if name in soft_banned:
                    messagebox.showerror("Error", f"{name} is soft-banned and cannot receive an extra hour as they have already logged in today.")
                    df.loc[df.index[df["Name"] == name].tolist()[0], current_date] += f" - Not Signed Out"
                else:
                    seconds_to_add = DEFAULT_HOURS * 60 * 60

                    df.loc[df.index[df["Name"] == name].tolist()[0], current_date] += f" - Not Signed Out: default {DEFAULT_HOURS} hour"
                    df.loc[df.index[df["Name"] == name].tolist()[0], "Hours"] = seconds_to_time(
                        time_to_seconds(df.loc[df.index[df["Name"] == name].tolist()[0], "Hours"]) + seconds_to_add)
                    print(f"\u001b[4m\u001b[1m\u001b[43;1m\u001b[30m{name} not signed out (default {DEFAULT_HOURS} hour)\u001b[0m")
            save_df = df.sort_values(by=["Hours"], ascending=False,
                                     key=lambda x: x.str.split(":").str.get(0).astype(int))
            save_df.to_csv(filename, index=False)
            message = gitUpload()
            save_df.to_csv(f"backup/{message}.csv", index=False)
            print(save_df)
            try:
                os.remove(filename)
                print(f"\u001b[32m{filename} removed successfully\u001b[0m")
            except OSError as error:
                print(error)
                print(f"\u001b[31m{filename} can not be removed\u001b[0m")
            root.destroy()
    else:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            sync(df)
            save_df = df.sort_values(by=["Hours"], ascending=False,
                                     key=lambda x: x.str.split(":").str.get(0).astype(int))
            save_df.to_csv(filename, index=False)
            message = gitUpload()
            save_df.to_csv(f"backup/{message}.csv", index=False)
            print(save_df)
            try:
                os.remove(filename)
                print(f"\u001b[32m{filename} removed successfully\u001b[0m")
            except OSError as error:
                print(error)
                print(f"\u001b[31m{filename} can not be removed\u001b[0m")
            root.destroy()


root.protocol("WM_DELETE_WINDOW", lambda: on_closing(df))

# Instructions
myLabel = Label(root, text="Find for your name:")

# Pick name
name_frame = Frame(root)
# Scrollbar
name_scrollbar = Scrollbar(name_frame, orient=VERTICAL)
name_box = Listbox(name_frame, yscrollcommand=name_scrollbar.set, width=36)
name_scrollbar.config(command=name_box.yview)

names = []
# Populate listbox with a specified max string length
for row in df.iterrows():
    if (row[1]['Name'] != "Shivam Aarya" and row[1]['Name'] != "Uddish Sood"):
        name_box.insert(END, f"{row[1]['Name']} - {row[1]['Hours']}")
    elif (row[1]['Name'] == "Shivam Aarya"):
        name_box.insert(END, f"{row[1]['Name']} - {row[1]['Hours']} (The best)")
    elif (row[1]['Name'] == "Uddish Sood"):
        name_box.insert(END, f"{row[1]['Name']} - {row[1]['Hours']} (The non-best)")
    names.append(row[1]["Name"])
    name_box.itemconfig(END, bg="light gray")
# Set initial selection
name_box.select_set(0)


# Buttons
def save():
    name = name_box.get(name_box.curselection())[:name_box.get(name_box.curselection()).index("-") - 1]
    if messagebox.askyesno("Save", f"Do you want to {r.get()} {name}?"):
        # TODO: Be able to sign in multiple people at once
        if r.get() == "sign in":
            if name in signed_in:
                messagebox.showerror("Error", f"{name} has already signed in")
            elif name in hard_banned:
                messagebox.showerror("Error", f"{name} is hard-banned and cannot sign in as they have already failed to log out.")
            else:
                signed_in.append(name)
                now = datetime.now()
                df.loc[df.index[df["Name"] == name].tolist()[0], current_date] = now.strftime("%H:%M:%S")
                print(f"\u001b[42;1m\u001b[1m{name}\u001b[0m signed in at {now.strftime('%H:%M:%S')}")
                name_box.itemconfig(name_box.curselection(), bg="palegreen")
        elif r.get() == "sign out":
            if name not in signed_in:
                messagebox.showerror("Error", f"{name} has not signed in")
            else:
                signed_in.remove(name)
                now = datetime.now()
                hours_to_add = time_difference(df.loc[df.index[df["Name"] == name].tolist()[0], current_date],
                                               now.strftime("%H:%M:%S"))
                df.loc[df.index[df["Name"] == name].tolist()[0], current_date] += f" - {now.strftime('%H:%M:%S')}"
                df.loc[df.index[df["Name"] == name].tolist()[0], "Hours"] = seconds_to_time(
                    time_to_seconds(df.loc[df.index[df["Name"] == name].tolist()[0], "Hours"]) + hours_to_add)
                print(f"\u001b[41;1m\u001b[30m\u001b[1m{name}\u001b[0m signed out at {now.strftime('%H:%M:%S')}")
                name_box.itemconfig(name_box.curselection(), bg="salmon")
        else:
            print("Error: invalid input")


radioFrame = LabelFrame(root)

r = StringVar()
r.set("sign in")

search = StringVar()
search.set("Searching: ")
searchLabel = Label(root, textvariable=search)

sign_in_radio = Radiobutton(radioFrame, text="Sign-in", variable=r, value="sign in", background="light green")
sign_out_radio = Radiobutton(radioFrame, text="Sign-out", variable=r, value="sign out", background="tomato")

save_button = Button(root, text="Save", command=save)

# Pack stuff
searchLabel.pack()
myLabel.pack()
name_scrollbar.pack(side=RIGHT, fill=Y)
name_box.pack(pady=10, padx=10, side=LEFT, fill=BOTH, expand=True)
name_box.focus_set()
name_frame.pack()
sign_in_radio.grid(row=0, column=0)
style = Style(root)
sign_out_radio.grid(row=0, column=1)
radioFrame.pack()
save_button.pack()

# Key bindings
root.bind("<Return>", lambda event: save())
root.bind("<Left>", lambda event: r.set("sign in"))
root.bind("<Right>", lambda event: r.set("sign out"))
root.bind("<Up>", lambda event: name_box.curselection()[0] - 1 if name_box.curselection()[0] > 0 else 0)
root.bind("<Down>",
          lambda event: name_box.curselection()[0] + 1 if name_box.curselection()[0] < len(names) - 1 else len(
              names) - 1)
root.bind("<Escape>", lambda event: on_closing(df))


def listbox_search(event):
    search.set(search.get() + event.char)
    search_string = search.get()[search.get().index(":") + 2:]
    found = False
    for i in range(len(names)):
        if names[i].lower().startswith(search_string):
            name_box.select_clear(0, END)
            name_box.select_set(i)
            event.widget.see(i)
            name_box.event_generate("<<ListboxSelect>>")
            name_box.see(i)
            found = True
            break
    if not found:
        for i in range(len(names)):
            if search_string in names[i].lower():
                name_box.select_clear(0, END)
                name_box.selection_set(i)
                name_box.see(i)
                found = True
                break
    if not found:
        search.set("Searching: " + event.char)


root.bind("<Key>", lambda event: listbox_search(event))

root.mainloop()

print("If you had any problems with this script, \u001b[4mplease inform Shivam.\u001b[0m")
