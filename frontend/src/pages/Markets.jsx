/**
 * Markets — the practice trading terminal.
 *
 * Four screens rather than one tabbed page, because the jobs are genuinely
 * different: read the account, work the book, place an order, review the risk.
 * They are routes so a screen is linkable and the back button behaves, and the
 * data each one needs is cached by key, so moving between them refetches
 * nothing.
 *
 * The site navigation is hidden for all of it — see `Terminal`.
 */
import { useParams } from 'react-router-dom'

import Analysis from './markets/Analysis'
import Explore from './markets/Explore'
import Overview from './markets/Overview'
import Positions from './markets/Positions'
import Terminal from './markets/Terminal'

const SCREENS = {
  overview: Overview,
  positions: Positions,
  trade: Explore,
  analysis: Analysis,
}

export default function Markets() {
  // `/markets/trade/:symbol` carries no `screen` param; a symbol in the URL
  // means the trade screen, showing that listing's ticket.
  const { screen, symbol } = useParams()
  const requested = symbol ? 'trade' : screen

  const Screen = SCREENS[requested] ?? Overview

  return (
    <Terminal>
      <Screen />
    </Terminal>
  )
}
