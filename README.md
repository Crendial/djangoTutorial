# Polling app
## This is an extended version of the polling app created in the official first Django app tutorial.
### It features:
- Cleaner UI.
- A simplistic way to avoid multiple votes per user.
- Pie charts in the results to show vote spread.
- QR code functionality for easy sharing.
- Support for multiple questions per poll.

## Example use cases:
### Case 1:
You want to collect data through public polls, so you decide to deploy the polling app.
First you'd go to {your site url}/admin to create new polls:
![Picture showing poll creation UI](mdImages/createPoll.png)

Simply click the add button next to polls on the left. Give the poll a release date, questions and choices, then save!
Do this for any polls you want to make and you'll have a full front page in no time! (Keep in mind that the front page has a poll limit of 6 and future polls aren't shown)

### To users, it would look like so:
Front page:
![Image of the poll apps front page](mdImages/pollIndex.png)
