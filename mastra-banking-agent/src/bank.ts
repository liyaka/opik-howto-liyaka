// Plain banking logic over the fictional records in data/. No framework and no
// tracing in here, so it is trivial to unit-test.
import accountsData from "../data/accounts.json" with { type: "json" };
import transactionsData from "../data/transactions.json" with { type: "json" };

export interface Card {
  card_id: string;
  last4: string;
  network: string;
  status: "active" | "frozen";
}

export interface Account {
  account_id: string;
  holder: string;
  type: string;
  currency: string;
  balance: number;
  cards: Card[];
}

export interface Transaction {
  txn_id: string;
  account_id: string;
  date: string;
  merchant: string;
  amount: number;
  category: string;
}

// Deep-copied so freezing a card in one run never mutates the imported JSON.
const accounts: Account[] = structuredClone(accountsData) as Account[];
const transactions: Transaction[] = transactionsData as Transaction[];

const norm = (id: string) => id.toUpperCase().trim();

export function resetBank(): void {
  accounts.splice(0, accounts.length, ...(structuredClone(accountsData) as Account[]));
}

export function getBalance(accountId: string) {
  const account = accounts.find((a) => a.account_id === norm(accountId));
  if (!account) return { error: `No account found with id ${accountId}.` };
  return {
    account_id: account.account_id,
    holder: account.holder,
    type: account.type,
    currency: account.currency,
    balance: account.balance,
    cards: account.cards.map((c) => ({ card_id: c.card_id, last4: c.last4, status: c.status })),
  };
}

export function listTransactions(accountId: string, limit = 5) {
  const id = norm(accountId);
  if (!accounts.some((a) => a.account_id === id)) {
    return { error: `No account found with id ${accountId}.` };
  }
  const items = transactions
    .filter((t) => t.account_id === id)
    .sort((a, b) => b.date.localeCompare(a.date) || b.txn_id.localeCompare(a.txn_id))
    .slice(0, limit);
  return { account_id: id, count: items.length, transactions: items };
}

export function freezeCard(cardId: string, reason: string) {
  const id = norm(cardId);
  for (const account of accounts) {
    const card = account.cards.find((c) => c.card_id === id);
    if (card) {
      const already = card.status === "frozen";
      card.status = "frozen";
      return {
        card_id: card.card_id,
        last4: card.last4,
        status: card.status,
        already_frozen: already,
        reason,
        next_step: "Card is blocked for new purchases immediately. A replacement ships in 5-7 business days.",
      };
    }
  }
  return { error: `No card found with id ${cardId}.` };
}
