import numpy as np
from sklearn.ensemble import RandomForestClassifier

from HPOlibConfigSpace.configuration_space import ConfigurationSpace
from HPOlibConfigSpace.hyperparameters import UniformFloatHyperparameter, \
    UniformIntegerHyperparameter, CategoricalHyperparameter, \
    UnParametrizedHyperparameter, Constant

from ParamSklearn.components.base import ParamSklearnClassificationAlgorithm
from ParamSklearn.util import DENSE, PREDICTIONS, SPARSE
# get our own forests to replace the sklearn ones
#from ParamSklearn.implementations import forest


class RandomForest(ParamSklearnClassificationAlgorithm):
    def __init__(self, n_estimators, criterion, max_features,
                 max_depth, min_samples_split, min_samples_leaf,
                 bootstrap, max_leaf_nodes, random_state=None, n_jobs=1):
        self.n_estimators = n_estimators
        self.estimator_increment = 10
        self.criterion = criterion
        self.max_features = max_features
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.bootstrap = bootstrap
        self.max_leaf_nodes = max_leaf_nodes
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.estimator = None

    def fit(self, X, y, sample_weight=None, refit=False):
        if self.estimator is None or refit:
            self.iterative_fit(X, y, n_iter=1, sample_weight=sample_weight,
                               refit=refit)

        while not self.configuration_fully_fitted():
            self.iterative_fit(X, y, n_iter=1, sample_weight=sample_weight)
        return self

    def iterative_fit(self, X, y, sample_weight=None, n_iter=1, refit=False):
        if refit:
            self.estimator = None

        if self.estimator is None:
            self.n_estimators = int(self.n_estimators)
            if self.max_depth == "None":
                self.max_depth = None
            else:
                self.max_depth = int(self.max_depth)
            self.min_samples_split = int(self.min_samples_split)
            self.min_samples_leaf = int(self.min_samples_leaf)
            if self.max_features not in ("sqrt", "log2", "auto"):
                num_features = X.shape[1]
                max_features = int(float(self.max_features) * (np.log(num_features) + 1))
                # Use at most half of the features
                max_features = max(1, min(int(X.shape[1] / 2), max_features))
            if self.bootstrap == "True":
                self.bootstrap = True
            else:
                self.bootstrap = False
            if self.max_leaf_nodes == "None":
                self.max_leaf_nodes = None

            # initial fit of only increment trees
            self.estimator = RandomForestClassifier(
                n_estimators=0,
                criterion=self.criterion,
                max_features=max_features,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                bootstrap=self.bootstrap,
                max_leaf_nodes=self.max_leaf_nodes,
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                warm_start=True)

        tmp = self.estimator # TODO I think we need to copy here!
        tmp.n_estimators += n_iter
        tmp.fit(X, y, sample_weight=sample_weight)
        self.estimator = tmp
        return self

    def configuration_fully_fitted(self):
        if self.estimator is None:
            return False

        return not len(self.estimator.estimators_) < self.n_estimators

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict_proba(X)

    @staticmethod
    def get_properties():
        return {'shortname': 'RF',
                'name': 'Random Forest Classifier',
                'handles_missing_values': False,
                'handles_nominal_values': False,
                'handles_numerical_features': True,
                'prefers_data_scaled': False,
                # TODO find out if this is good because of sparcity...
                'prefers_data_normalized': False,
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'handles_sparse': True,
                'input': (DENSE, SPARSE),
                'output': PREDICTIONS,
                # TODO find out what is best used here!
                # But rather fortran or C-contiguous?
                'preferred_dtype': np.float32}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        #n_estimators = UniformIntegerHyperparameter(
        #    "n_estimators", 10, 100, default=10)
        n_estimators = Constant("n_estimators", 100)
        criterion = CategoricalHyperparameter(
            "criterion", ["gini", "entropy"], default="gini")
        #max_features = UniformFloatHyperparameter(
        #    "max_features", 0.01, 0.5, default=0.2)
        max_features = UniformFloatHyperparameter(
            "max_features", 0.5, 5, default=1)
        max_depth = UnParametrizedHyperparameter("max_depth", "None")
        min_samples_split = UniformIntegerHyperparameter(
            "min_samples_split", 2, 20, default=2)
        min_samples_leaf = UniformIntegerHyperparameter(
            "min_samples_leaf", 1, 20, default=1)
        max_leaf_nodes = UnParametrizedHyperparameter("max_leaf_nodes", "None")
        bootstrap = CategoricalHyperparameter(
            "bootstrap", ["True", "False"], default="True")
        cs = ConfigurationSpace()
        cs.add_hyperparameter(n_estimators)
        cs.add_hyperparameter(criterion)
        cs.add_hyperparameter(max_features)
        cs.add_hyperparameter(max_depth)
        cs.add_hyperparameter(min_samples_split)
        cs.add_hyperparameter(min_samples_leaf)
        cs.add_hyperparameter(max_leaf_nodes)
        cs.add_hyperparameter(bootstrap)
        return cs
