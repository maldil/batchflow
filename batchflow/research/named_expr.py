""" Contains named expression classes for Research """

from .results import Results
from ..named_expr import NamedExpression

class ResearchNamedExpression(NamedExpression):
    """ NamedExpression base class for Research objects """
    def __init__(self, name=None):
        super().__init__(name=name)

    def _get(self, **kwargs):
        name = self._get_name(**kwargs)
        return name, kwargs

class ResearchExecutableUnit(ResearchNamedExpression):
    """ NamedExpression for ExecutableUnit """
    def _get(self, **kwargs):
        _, kwargs = super()._get(**kwargs)
        experiment = kwargs['experiment']
        return experiment

    def get(self, **kwargs):
        experiment = self._get(**kwargs)
        if isinstance(experiment, (list, tuple)):
            _experiment = experiment
        else:
            _experiment = [experiment]
        if self.name is not None:
            res = [item[self.name] for item in _experiment]
            if len(_experiment) == 1:
                return res[0]
            return res
        return experiment

class ResearchPipeline(ResearchExecutableUnit):
    """ NamedExpression for Pipeline in Research """
    def __init__(self, name=None, root=False):
        super().__init__(name)
        self.root = root

    def get(self, **kwargs):
        if self.name is None:
            raise ValueError('`name` must be defined for RP expressions')
        res = super().get(**kwargs)
        attr = 'root_pipeline' if self.root else 'pipeline'

        if isinstance(res, list):
            return [getattr(item, attr) for item in res]
        return getattr(res, attr)

class ResearchIteration(ResearchNamedExpression):
    """ NamedExpression for iteration of Research """
    def _get(self, **kwargs):
        _, kwargs = super()._get(**kwargs)
        return kwargs['iteration']

    def get(self, **kwargs):
        iteration = self._get(**kwargs)
        return iteration

class ResearchConfig(ResearchExecutableUnit):
    """ NamedExpression for Config of the ExecutableUnit """
    def get(self, **kwargs):
        if self.name is None:
            raise ValueError('`name` must be defined for RC expressions')
        res = super().get(**kwargs)

        if isinstance(res, list):
            return [getattr(item, 'config') for item in res]
        return getattr(res, 'config')

class ResearchPath(ResearchNamedExpression):
    """ NamedExpression for path to the Research """
    def _get(self, **kwargs):
        _, kwargs = super()._get(**kwargs)
        return kwargs['path']

    def get(self, **kwargs):
        path = self._get(**kwargs)
        return path

class ResearchResults(ResearchNamedExpression):
    """ NamedExpression for Results of the Research """
    def __init__(self, name=None, *args, **kwargs):
        super().__init__(name)
        self.args = args
        self.kwargs = kwargs

    def _get(self, **kwargs):
        _, kwargs = super()._get(**kwargs)
        if kwargs['path'] is None:
            path = kwargs['job'].research_path
        else:
            path = kwargs['path']
        return path

    def get(self, **kwargs):
        path = self._get(**kwargs)
        return Results(path=path).load(*self.args, **self.kwargs)
