// >>> WARNING THIS PAGE WAS AUTO-GENERATED - DO NOT EDIT!!! <<<

import QuestionPage from '../../question.page'

class VisitorNamePage extends QuestionPage {

  constructor() {
    super('visitor-name')
  }

  setVisitorFirstName(value) {
    browser.setValue('[name="visitor-first-name"]', value)
    return this
  }

  getVisitorFirstName(value) {
    return browser.element('[name="visitor-first-name"]').getValue()
  }

  setVisitorLastName(value) {
    browser.setValue('[name="visitor-last-name"]', value)
    return this
  }

  getVisitorLastName(value) {
    return browser.element('[name="visitor-last-name"]').getValue()
  }

}

export default new VisitorNamePage()
