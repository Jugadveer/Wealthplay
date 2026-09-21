/**
 * Markets: the practice portfolio, the stock list, and analysis.
 *
 * One page with three tabs rather than three routes, so switching does not
 * remount and refetch. The tab bar renders once — the old portfolio drew two
 * stacked tab bars because a parent and a child each rendered their own.
 */
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { PageHeader, Tabs } from '../ui'
import Analysis from './markets/Analysis'
import Explore from './markets/Explore'
import Holdings from './markets/Holdings'

const TABS = [
  { value: 'holdings', label: 'Holdings' },
  { value: 'explore', label: 'Explore' },
  { value: 'analysis', label: 'Analysis' },
]

const PANELS = { holdings: Holdings, explore: Explore, analysis: Analysis }

export default function Markets() {
  // `/markets/explore/:symbol` has no `tab` param, so a symbol in the URL
  // implies the explore tab.
  const { tab, symbol } = useParams()
  const navigate = useNavigate()

  const requested = symbol ? 'explore' : tab
  const active = PANELS[requested] ? requested : 'holdings'
  const Panel = PANELS[active]

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow="Practice account"
        title="Markets"
        lede="₹50,000 of virtual money over real listings and a set of simulated stocks. Nothing here touches real money."
      />

      <div className="mt-6">
        <Tabs items={TABS} value={active} onChange={(value) => navigate(`/markets/${value}`)} />
      </div>

      <div className="mt-6">
        <Panel />
      </div>
    </div>
  )
}
