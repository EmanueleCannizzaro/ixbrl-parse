document.addEventListener('DOMContentLoaded', function() {
    console.log('XBRL Data Display loaded');

    function populateFactsTables() {
        const factsDataElement = document.getElementById('xbrl-facts-data');
        if (!factsDataElement) {
            console.error('Facts data element not found');
            return;
        }

        const facts = JSON.parse(factsDataElement.textContent);
        const allFactsContainer = document.querySelector('#all-facts');
        const balanceSheetContainer = document.querySelector('#balance-sheet');
        const incomeStatementContainer = document.querySelector('#income-statement');
        const cashFlowContainer = document.querySelector('#cash-flow');

        const groupedFacts = groupFactsByContextRef(facts);

        populateContainer(allFactsContainer, groupedFacts);
        populateContainer(balanceSheetContainer, filterFactsByCategory(groupedFacts, isBalanceSheetFact));
        populateContainer(incomeStatementContainer, filterFactsByCategory(groupedFacts, isIncomeStatementFact));
        populateContainer(cashFlowContainer, filterFactsByCategory(groupedFacts, isCashFlowFact));
    }

    function groupFactsByContextRef(facts) {
        return facts.reduce((groups, fact) => {
            const group = groups[fact.contextRef] || [];
            group.push(fact);
            groups[fact.contextRef] = group;
            return groups;
        }, {});
    }

    function populateContainer(container, groupedFacts) {
        for (const [contextRef, facts] of Object.entries(groupedFacts)) {
            const contextGroup = document.createElement('div');
            contextGroup.className = 'context-group mb-4';
            
            const contextHeader = document.createElement('h5');
            contextHeader.textContent = `Context: ${contextRef}`;
            contextGroup.appendChild(contextHeader);

            const table = document.createElement('table');
            table.className = 'table table-striped table-hover';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Concept</th>
                        <th>Value</th>
                        <th>Unit Ref</th>
                        <th>Decimals</th>
                    </tr>
                </thead>
                <tbody>
                    ${facts.map(fact => `
                        <tr>
                            <td>${fact.concept}</td>
                            <td>${fact.value}</td>
                            <td>${fact.unitRef || 'N/A'}</td>
                            <td>${fact.decimals || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;

            contextGroup.appendChild(table);
            container.appendChild(contextGroup);
        }
    }

    function filterFactsByCategory(groupedFacts, categoryFilter) {
        const filteredGroups = {};
        for (const [contextRef, facts] of Object.entries(groupedFacts)) {
            const filteredFacts = facts.filter(fact => categoryFilter(fact.concept));
            if (filteredFacts.length > 0) {
                filteredGroups[contextRef] = filteredFacts;
            }
        }
        return filteredGroups;
    }

    function isBalanceSheetFact(concept) {
        const balanceSheetKeywords = ['Assets', 'Liabilities', 'Equity', 'Inventory', 'Receivables'];
        return balanceSheetKeywords.some(keyword => concept.includes(keyword));
    }

    function isIncomeStatementFact(concept) {
        const incomeStatementKeywords = ['Revenue', 'Expenses', 'Income', 'Profit', 'Loss'];
        return incomeStatementKeywords.some(keyword => concept.includes(keyword));
    }

    function isCashFlowFact(concept) {
        const cashFlowKeywords = ['CashFlow', 'Operating', 'Investing', 'Financing'];
        return cashFlowKeywords.some(keyword => concept.includes(keyword));
    }

    function implementSearch() {
        const searchInput = document.getElementById('factsSearch');
        const contextGroups = document.querySelectorAll('.context-group');

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            contextGroups.forEach(group => {
                const rows = group.querySelectorAll('tbody tr');
                let groupVisible = false;
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    const visible = text.includes(searchTerm);
                    row.style.display = visible ? '' : 'none';
                    if (visible) groupVisible = true;
                });
                group.style.display = groupVisible ? '' : 'none';
            });
        });
    }

    populateFactsTables();
    implementSearch();

    // Add sorting functionality to the tables
    document.querySelectorAll('#factsTables th').forEach(th => th.addEventListener('click', (() => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        Array.from(tbody.querySelectorAll('tr'))
            .sort((a, b) => {
                const aValue = a.children[th.cellIndex].textContent;
                const bValue = b.children[th.cellIndex].textContent;
                return aValue.localeCompare(bValue, undefined, {numeric: true, sensitivity: 'base'});
            })
            .forEach(tr => tbody.appendChild(tr));
    })));
});