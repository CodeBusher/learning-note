import util
import numpy as np


def calc_grad(X, Y, theta):
    """Compute the gradient of the loss with respect to theta."""

    # Start your code here
    
    # End your code here

    return grad


def logistic_regression(X, Y):
    """Train a logistic regression model."""
    theta = np.zeros(X.shape[1])
    learning_rate = 0.1

    i = 0
    
    # Start your code here
    
    # End your code is here

def main():
    print('==== Training model on data set 1 ====')
    X1, Y1 = util.load_csv('dataset1.csv', add_intercept=True)
    theta = logistic_regression(X1, Y1)


if __name__ == '__main__':
    main()
