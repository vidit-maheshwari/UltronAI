#include <stdio.h>
#include <limits.h>

int maxProfit(int* prices, int pricesSize) {
    int buy1 = INT_MAX;
    int sell1 = 0;
    int buy2 = INT_MAX;
    int sell2 = 0;

    for (int i = 0; i < pricesSize; i++) {
        buy1 = (buy1 < prices[i]) ? buy1 : prices[i];
        sell1 = (sell1 > prices[i] - buy1) ? sell1 : prices[i] - buy1;
        buy2 = (buy2 < sell1 - prices[i]) ? buy2 : sell1 - prices[i];
        sell2 = (sell2 > buy2 + prices[i]) ? sell2 : buy2 + prices[i];
    }

    return sell2;
}

int main() {
    // Example usage:
    int prices[] = {3, 3, 5, 0, 0, 3, 1, 4};
    int n = sizeof(prices) / sizeof(prices[0]);
    printf("Maximum profit: %d\n", maxProfit(prices, n));
    return 0;
}