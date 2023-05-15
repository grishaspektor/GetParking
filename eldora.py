#!/usr/bin/python3

#These are the details For the final form
#firstNameStr = 'Tracy'
#lastNameStr = 'Transfer'
#emailStr = 'tracy.transfer@gmail.com'
#licensePlateStr = 'asd234'
#stateStr = 'colorado'
#
##This is the desired date important month first number last. Does not validate anything - just trusts user
##Currently does not go to the month - assumes that the month is currently opened in the browser
#dateStr = 'January 9'
##will try to reserve earlier or equal to the # timeSlot
##where 1 = 9am; 2 = 11am; 3 <=>1:30pm; 4 <=>2:30pm
#timeSlot = 3

import re
import traceback

import time
import argparse
from bs4 import BeautifulSoup

# Import webdriver to initialise a browser
from selenium import webdriver
from selenium.webdriver import ActionChains

class Reservation:
    def __init__(self,firstNameStr, lastNameStr, emailStr, licensePlateStr, stateStr, dateStr, timeSlot):
        # website that we want to scrap
        self.url = "https://www.eldora.com/plan-your-trip/getting-here/parking-reservations"

        # Initialize webdriver and put the path where download the driver
        self.driver = webdriver.Chrome(r'./chromedriver')

        # Launch Chrome and pass the url
        while True:
            try:
                self.driver.get(self.url)
                #self.driver.maximize_window()
                
                refreshAttemptWait =8 #sec
                waitForRefreshCompletion = 8#sec
                        
                # loop over this process until goal achieved (?)    
                # now go to the caldnearFrame and press the forwardButton
                dayAttemptCounter = 1
                while True:
                    self.__goToCalendarIFrame()
                    self.__selectMonth(dateStr)
                    if not self.__clickIfMyDayAvailable(dateStr): #day not available
                        print('Day Not Available, Attempt#: ', dayAttemptCounter)
                        time.sleep(refreshAttemptWait) # <todo>Just a wait time between refreshes
                        self.driver.refresh()
                        time.sleep(waitForRefreshCompletion) #<todo> !! how long to wait until refresh is complete- currently just a number but should ideally change to polling of some element existence https://stackoverflow.com/questions/28026470/python-selenium-wont-wait-for-my-website-to-refresh 
                        dayAttemptCounter +=1
                        
                    else: 
                        print('Day Available!')
                        #now try reserve the slot - currently reserves the earliest available.
                        if (not self.__selectReservationSlotsIfAvailable(timeSlot)) : #slot not available
                            print('slot not available, Attempt#: ', dayAttemptCounter)
                            self.driver.refresh()
                            time.sleep(waitForRefreshCompletion) #<todo> !! how long to wait until refresh is complete- currently just a number but should ideally change to polling of some element existence https://stackoverflow.com/questions/28026470/python-selenium-wont-wait-for-my-website-to-refresh 
                            dayAttemptCounter +=1
                        else :
                            print('slot available, filling form')
                            time.sleep(3)
                            self.__fillFormAndFinish(firstNameStr, lastNameStr, emailStr, licensePlateStr, stateStr)
                            return
            except Exception as e:
                print(repr(e))
                print(traceback.print_exc())
                time.sleep(5)
                pass
        #self.driver.close();
        
    def __goToCalendarIFrame(self):
        #Switch to the calendar iframe (currently explicit..)

        #go to the top hirearchy level
        self.driver.switch_to.default_content() 
        #go to the calendar iframe
        calendarFrame = self.driver.find_element_by_xpath('/html/body/div[1]/div/div[1]/div/main/cms-level0/section[2]/cms-level1/div[2]/section[2]/div[5]/cms-level3/section/ui-section[1]/div/div/ui-html[2]/div/p/iframe')
        self.driver.switch_to.frame(calendarFrame)
        # get the monthback and month forward buttons
        time.sleep(10)
        backButton = self.driver.find_element_by_xpath('/html/body/div/div/div/div/div[3]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div[1]')
        self.forwardButton = self.driver.find_element_by_xpath('/html/body/div/div/div/div/div[3]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div[2]')
    
    def __selectMonth(self, dateStr):
        #check what month are we - this one is explicit xpath because of some bug that "displays" 
        #several months in the same page
        #Assumes: going only forward in months
        correctMonthFlag = False
        #spilt the desired date to isolate month and date
        parsedDateInput = dateStr.split()
        # go to the proper month, Assumes that going forward only.
        while (not correctMonthFlag):
            monthName = self.driver.find_element_by_xpath('/html/body/div/div/div/div/div[3]/div/div/div/div[2]/div/div/div/div/div[2]/div[2]/div/div[2]/div/div')
            monthName.get_attribute('text')
            if  (parsedDateInput[0].upper() in monthName.text) or ((parsedDateInput[0] in monthName.text)):
                correctMonthFlag = True
            else :
                self.forwardButton.click()   
    
    def __clickIfMyDayAvailable(self,dateStr):
        #The calendar is a table, due to a bug there are 3 tables prev. month, curr. month and next month. so list[1] is cuurent month
        availableFlag = False
        tableList = self.driver.find_elements_by_tag_name('table')
        print("sleep now")
        time.sleep(3)
        searchStr = dateStr
        notAvailableStr = 'Not available.'
        # Go over the table for each day
        for row in tableList[1].find_elements_by_css_selector('tr'):
            for cell in row.find_elements_by_tag_name('td'):
                statusString = str(cell.get_attribute('aria-label'))
                print(statusString)
                if searchStr+',' in statusString: #ensures that e.g. "January 2," is found but not "January 20,"
#                     print('here')
                    if notAvailableStr not in statusString:
#                         print("Ha!")
                        cell.click()
                        availableFlag = True
                    break;
        #             else : # if here but not available then refresh
        #                 driver.refresh()
        #Change this so that if not available it waits, refreshes the page and does it all over.
        return availableFlag
   
    def __selectReservationSlotsIfAvailable(self,timeSlot):
        # Now look at the opened dialogue and check which one is available
        #selects and books if available returns False if not

        #find the opened window with the time slots that opens after clicking on the available day
        menu = self.driver.find_elements_by_tag_name('div')
        for element in menu:
            if 'hidden d-lg-block col-xs-12 col-md-4' in element.get_attribute('class'):
#                 print('menu found')
                selectedElement = element
                break;
                
        #Now I need to check which one is available and select the earliest one
        #The available ones are    "event-picker-choice"
        #The UN-available ones are "event-picker-choice disabled"
        #The selected one is       "event-picker-choice checked"
        results = selectedElement.find_elements_by_class_name('event-picker-choice')
#         this prints out the slots
#         for element2 in results:
#             temp = element2.find_element_by_tag_name('div')
#             print(temp.text, ' ', temp.get_attribute('class'))
        slotCounter = 0
        for element2 in results:
            slotCounter +=1
            if (slotCounter <= timeSlot) and ('disabled' not in str(element2.get_attribute('class'))):
                print('selected ', element2.get_attribute("textContent"))
                element2.click()
                break;
            if slotCounter == 4:
                return False
                #######<todo>this way it selects the earliest available slot
        
        # press the select button and go to next screen
        #Press the button for next menu
        bttn = self.driver.find_element_by_class_name("event-picker-button")
        bttn.click()
        time.sleep(2) #<todo> poll if passed to ext 
        # press the 'book now' button in the new stupid window
        #go to the "book now" iframe
        self.driver.switch_to.default_content() 

        frames = self.driver.find_elements_by_tag_name('iframe')
        for aFrame in frames:
            if 'widget.arrive.com' in aFrame.get_attribute('src'):
        #         print(aFrame.get_attribute('src'))
                self.driver.switch_to.frame(aFrame)
                break;
        #find the button and press it
        fields = self.driver.find_elements_by_tag_name('div')
        for aField in fields:
            if 'location-book-now clickable' in aField.get_attribute('class'):
                aField.click()
                time.sleep(1)
                return True;
                break;
        
        
    def __fillFormAndFinish(self,firstNameStr, lastNameStr, emailStr, licensePlateStr, stateStr):
        #Now we need to fill the form...
        self.driver.switch_to.default_content() 

        frames = self.driver.find_elements_by_tag_name('iframe')
        for aFrame in frames:
            if 'widget.arrive.com' in aFrame.get_attribute('src'):
                self.driver.switch_to.frame(aFrame)
                break;
        self.driver.find_element_by_id('firstName').send_keys(firstNameStr)
        self.driver.find_element_by_id('lastName').send_keys(lastNameStr)
        self.driver.find_element_by_id('email').send_keys(emailStr)

        fields = self.driver.find_elements_by_tag_name('input')
        len(fields)
        for field in fields:
            if field.get_attribute('maxlength') != None:
                field.send_keys(licensePlateStr)
        fields[4].send_keys(stateStr)
        # find and click the checkout button
        self.driver.find_element_by_class_name('checkout-button').click()
        #<todo> verify something
        print('Filled and Booked!')
        time.sleep(10)
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get parking.')
    parser.add_argument('--first_name', type=str, required=True)
    parser.add_argument('--last_name', type=str, required=True)
    parser.add_argument('--email', type=str, required=True)
    parser.add_argument('--license_plate', type=str, required=True)
    parser.add_argument('--state', type=str, required=True)
    parser.add_argument('--date', type=str, required=True)
    parser.add_argument('--time_slot', type=int, required=True)
    args = parser.parse_args()
    
    reservation = Reservation(
        args.first_name,
        args.last_name,
        args.email,
        args.license_plate,
        args.state,
        args.date,
        args.time_slot)
