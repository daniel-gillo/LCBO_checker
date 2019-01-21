#!/usr/bin/env python3
"""Checks the LCBO for rare items, to see if they are in stock again.
Has two options of notifying you, either via email, or creating a 
file on your desktop.
You can set the items to check by adding them into the links.txt file.
"""

import datetime
import smtplib
import time
import urllib.request

__author__ = "Daniel Gillo"
__copyright__ = "Copyright 2019"
__credits__ = ["Daniel Gillo"]
__license__ = "GNU GPLv3"
__version__ = "1.5"
__maintainer__ = "Daniel Gillo"
__email__ = "danigillo@gmail.com"
__status__ = "Production"


class check:
    # All outputs should go to that file now
    # fp = codecs.open("logger.txt", "a+", "ISO-8859-1")
    # sys.stdout = fp
    # sys.stderr = fp

    def main(self):
        """ Main function, runs everything infinitely. """
        TIMEOUT = 15  # Server will kick us for resource overload if too low
        MESSAGES = 1  # How many messages per bottle I wanna get.
        SEND_EMAIL = False  # Want to get an email with the details?
        WRITE_FILES = True  # Want to get flooded with files instead?
        trace = []
        in_a = "http://www.lcbo.com/webapp/wcs/stores/servlet/ProductStore" \
               "InventoryView?catalogId=10001&langId=-1&partNumber="
        in_b = "&storeId=10151"

        # Open list with list of bottles to check
        # Add the url of the LCBO item page to links.txt
        with open("links.txt", "r") as file:
            bottles = file.readlines()
            for bottle in bottles:
                if bottle.startswith("#") or len(bottle) < 9:
                    # If a comment line, or non-url string is present, ignore
                    continue
                bottle = bottle.rstrip("\n")
                b = bottle.rsplit('/', 1)[1]
                b = in_a + b + in_b
                trace.append([bottle, b])

        for whiskey in trace:
            whiskey.append(MESSAGES)
        left_to_send = len(trace) * MESSAGES - 1

        # Here we go, now the action begins!
        first = False
        try:
            for whiskey in trace:
                # Run the timeout, only after we've checked one link already.
                # Moved it here so we don't timeout after the last link.
                if first:
                    time.sleep(TIMEOUT)
                else:
                    first = True

                # I have forgotten why I originally included left_to_send.
                left_to_send -= 1
                # Check if any we sent all messages for that whiskey.
                # if not whiskey[2]:
                #    continue
                if check.in_store(self, whiskey[1]) or \
                        check.web(self, whiskey[0]):
                    whiskey[2] -= 1
                    print(str(whiskey[0]) + " is in stock")
                    # Notify user by either email or writing files to desktop
                    if SEND_EMAIL and check.send_mail(self, whiskey[0]):
                        print("###### email didn't send about change")
                    if WRITE_FILES:
                        check.write_results(self, whiskey[0])
                else:
                    print(str(whiskey[0]) + " is not stocked!")

        except Exception as e:
            print("###### Some error happened that wasn't caught!\n" + str(e))
            # Reset variables
            change = 0

    def web(self, link):
        """ Checks if the LCBO changed the buyable type of the item.
            Sends an email if item can be bought. """
        # print(link[33:])
        buyable = False
        code_we_want = None
        #  url_open returns None if url wasn't opened.
        file = check.open_url(self, link)
        if file is None:
            return buyable

        for line in file:
            line = line.decode("utf-8")
            if "<!-- buyableType = " in line:
                code_we_want = line
                break

        # <!-- buyableType = <1,2,3>; buyable = <true,false>;
        # onlineInventory: type 1 => Online exclusive, type 2 => Out of Stock
        # type 3 => In-store Only
        # buyable true => online sale, buyable false => not for sale online
        # onlineInventory is blank, get this via separate ajax request.
        if "1" in code_we_want:  # or "3" in code_we_want:
            print(code_we_want)
            buyable = True
        return buyable

    def in_store(self, link):
        """ Returns how many items of a product are
            purchasable in all LCBO stores. """
        # print(link)
        in_stock = False
        # url_open returns None if url wasn't opened
        file = check.open_url(self, link)
        if file:
            # Check all stores inventory
            line_count = 0
            for line in file:
                line_count += 1
                if 60 < line_count < 134:
                    line = line.decode("utf-8")
                    # This line means there is NO inventory
                    if line.startswith("\t\t\t\t\t\t<tr><td colspan=\"3\" "
                                       "class=\"no-inventory"):
                        break
                    # We found the line listing store specific inventory
                    elif line.startswith("\t\t\t\t\t\t\t\t\t<p class="
                                         "\"item-details\">"):
                        in_stock = True
                        break
        return in_stock

    def open_url(self, link):
        """ Opens a url it's given and does error checking. Returns
            file pointer to link if opened, None object otherwise """
        # All outputs should go to that file now
        # fp = codecs.open("logger.txt", "a+", "ISO-8859-1")
        # sys.stdout = fp
        # sys.stderr = fp
        attempts = 3
        file = None
        while attempts:
            try:
                # The line that actually opens the url
                file = urllib.request.urlopen(link)
                break
            # If there's an error, attempt 2 or 3 times.
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                print("###### urllib.error\n" + str(e) + "\n" + link)
                attempts -= 1
                # If we encounter a 404 error, no need to try again
                if "404" in str(e) or "403" in str(e):
                    attempts = 0
                elif "408" in str(e):
                    attempts -= 2
            except (TimeoutError, http.client.RemoteDisconnected) as e:
                print("###### TimeoutError\n" + str(e) + "\n" + link)
                attempts -= 2
            except Exception as e:
                print("###### Other Error\n" + str(e) + "\n" + link)
                attempts -= -1
        return file

    def send_mail(self, link):
        """ If a change happened send me an email """
        attempts = 3
        not_sent = True
        while not_sent:
            # Try block in case there is an error sending the email.
            try:
                msg = "Availability might have changed.\nCheck LCBO!\n" + link
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login("youremail@gmail.com", "You know, your password!")
                # sever.sendmail(sender, recepient, message)
                server.sendmail("youremail@gmail.com",
                                "youremail@gmail.com", msg)
                # server.sendmail("youremail@gmail.com",
                #                "someotheremail@gmail.com", msg)
                server.quit()
                not_sent = False
            except Exception as e:
                print("###### Error Sending email\n" + str(e))
                attempts -= 1
                if attempts > 0:
                    continue
                break
        return not_sent

    def write_results(self, link, no_files=3):
        """ Writes a given number of empty files to your desktop
            to notify you of a new arrival.
            By default it writes 3 files. (See no_files variables above) """
        location = "C:\\Users\\Your_Username\\Desktop\\" + "A-Bottles-back-"
        location += link.rsplit("/", 2)[1]
        while no_files:
            with open((location + str(-no_files) + ".txt"), "a") as file:
                file.write(link + "\t As of " +
                           datetime.datetime.today().strftime('%Y-%m-%d') +
                           " is now available again!\n")
            no_files -= 1
        return True


r = check()
r.main()
