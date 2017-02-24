import chai from 'chai'
import {openQuestionnaire} from '../helpers'
import RadioMandatoryPage from '../pages/surveys/radio/radio-mandatory.page'
import RadioNonMandatory from '../pages/surveys/radio/radio-non-mandatory.page'
import SummaryPage from '../pages/surveys/radio/summary.page'

const expect = chai.expect

describe('Radio button with "other" option', function() {

  var radio_schema = 'test_radio.json';

  it('Given an "other" option is available, when the user clicks the "other" option then other input should be visible', function() {
    //Given
    openQuestionnaire(radio_schema)

    //When
    RadioMandatoryPage.clickOther()

    // Then
    expect(RadioMandatoryPage.otherInputFieldExists()).to.be.true
  })

  it('Given I enter a value into the other input field, when I submit the page, then value should be displayed on the summary.', function() {
    //Given
    openQuestionnaire(radio_schema)

    // When
    RadioMandatoryPage.clickOther().setOtherInputField('Hello').submit()
    RadioNonMandatory.submit(); // Skip second page.


    //Then
    expect(SummaryPage.getMandatoryAnswer()).to.contain('Hello')
  })

  it('Given a mandatory radio answer, when I select "Other" and submit without completing the other input field, then an error must be displayed.', function() {
    //Given
    openQuestionnaire(radio_schema)

    //When
    RadioMandatoryPage.clickOther().submit();

    //Then
    expect(RadioMandatoryPage.errorExists()).to.be.true
  })

  it('Given a mandatory radio answer and error is displayed for other input field, when I enter value and submit page, then the error should be cleared.', function() {
    //Given
    openQuestionnaire(radio_schema);

    //When
    RadioMandatoryPage.clickOther().submit();
    expect(RadioMandatoryPage.errorExists()).to.be.true
    RadioMandatoryPage.clickOther().setOtherInputField('Other Text').submit()

    //Then
    expect(RadioNonMandatory.errorExists()).to.be.false
  })

  it('Given I have previously added text in other texfiled and saved, when I change the awnser to a diffrent answer, then the text entered in other field must be wiped.', function() {
    //Given
    openQuestionnaire(radio_schema);

    //When
    RadioMandatoryPage.clickOther().setOtherInputField('Other Text').submit()
    RadioNonMandatory.clickTopPrevious()
    RadioMandatoryPage.clickRadioMandatoryAnswerBacon().submit()
    RadioNonMandatory.clickTopPrevious()

    //Then
    RadioMandatoryPage.clickOther()
    expect(RadioMandatoryPage.getOtherInputField()).to.equal('')
  })

})
