# Incoming message ids.
TICK_PRICE               = 1
TICK_SIZE                = 2
ORDER_STATUS             = 3
ERR_MSG                  = 4
OPEN_ORDER               = 5
ACCT_VALUE               = 6
PORTFOLIO_VALUE          = 7
ACCT_UPDATE_TIME         = 8
NEXT_VALID_ID            = 9
CONTRACT_DATA            = 10
EXECUTION_DATA           = 11
MARKET_DEPTH     	     = 12
MARKET_DEPTH_L2          = 13
NEWS_BULLETINS    	     = 14
MANAGED_ACCTS    	     = 15
RECEIVE_FA    	         = 16
HISTORICAL_DATA          = 17
BOND_CONTRACT_DATA       = 18
SCANNER_PARAMETERS       = 19
SCANNER_DATA             = 20
TICK_OPTION_COMPUTATION  = 21
TICK_GENERIC             = 45
TICK_STRING              = 46
TICK_EFP                 = 47
CURRENT_TIME             = 49
REAL_TIME_BARS           = 50
FUNDAMENTAL_DATA         = 51
CONTRACT_DATA_END        = 52
OPEN_ORDER_END           = 53
ACCT_DOWNLOAD_END        = 54
EXECUTION_DATA_END       = 55
DELTA_NEUTRAL_VALIDATION = 56
TICK_SNAPSHOT_END        = 57
MARKET_DATA_TYPE         = 58
COMMISSION_REPORT        = 59

MESSAGE_SIZES = {
    TICK_PRICE:               5,
    TICK_SIZE:                3,
    ORDER_STATUS:             10,
    ERR_MSG:                  3,
    OPEN_ORDER:               None,
    ACCT_VALUE:               4,
    PORTFOLIO_VALUE:          17,
    ACCT_UPDATE_TIME:         1,
    NEXT_VALID_ID:            1,
    CONTRACT_DATA:            None,
    EXECUTION_DATA:           None,
    MARKET_DEPTH:             None,
    MARKET_DEPTH_L2:          None,
    NEWS_BULLETINS:           None,
    MANAGED_ACCTS:            1,
    RECEIVE_FA:               None,
    HISTORICAL_DATA:          None,
    BOND_CONTRACT_DATA:       None,
    SCANNER_PARAMETERS:       None,
    SCANNER_DATA:             None,
    TICK_OPTION_COMPUTATION:  10,
    TICK_GENERIC:             3,
    TICK_STRING:              3,
    TICK_EFP:                 9,
    CURRENT_TIME:             None,
    REAL_TIME_BARS:           None,
    FUNDAMENTAL_DATA:         None,
    CONTRACT_DATA_END:        None,
    OPEN_ORDER_END:           None,
    ACCT_DOWNLOAD_END:        1,
    EXECUTION_DATA_END:       None,
    DELTA_NEUTRAL_VALIDATION: None,
    TICK_SNAPSHOT_END:        None,
    MARKET_DATA_TYPE:         None,
    COMMISSION_REPORT:        None,
}

