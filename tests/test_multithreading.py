# Copyright (C) 2018 Leiden University Medical Center
# This file is part of pytest-workflow
#
# pytest-workflow is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pytest-workflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pytest-workflow.  If not, see <https://www.gnu.org/licenses/

import time

import pytest

import yaml

# Sleep time was chosen such that pytest-workflow overhead should not influence
# the results. Running pytest with empty sleep commands takes about 0.444
# seconds on pytest-workflow 0.2 (without multithreading. So we should be a
# a safe margin above that.
SLEEP_TIME = 0.75
SLEEP_COMMAND = f"sleep {SLEEP_TIME}"

MULTHITHREADED_TEST = [
    dict(name="Doornroosje", command=SLEEP_COMMAND),
    dict(name="Dornröschen", command=SLEEP_COMMAND),
    dict(name="Little Briar Rose", command=SLEEP_COMMAND),
    dict(name="Rose d'épine", command=SLEEP_COMMAND),
]


@pytest.mark.parametrize(["threads"], [(1,), (2,), (4,)])
def test_multithreaded(threads, pytester):
    test = MULTHITHREADED_TEST
    test_number = len(test)
    pytester.makefile(".yml", test=yaml.safe_dump(test))

    # Calculate how many iterations are needed to process all the tests
    # For example: 4 tests with 2 threads. 2 can be finished simultaneously
    # then the next 2. That is 2 iterations. With 4 threads it is 1 iteration.
    # With 3 threads, it is also 2 iterations.
    iterations = (test_number // threads if (test_number % threads == 0)
                  else test_number // threads + 1)

    start_time = time.time()
    pytester.runpytest("-v", "--wt", str(threads))
    end_time = time.time()
    completion_time = end_time - start_time
    # If the completion time is shorter than (iterations * SLEEP_TIME), too
    # many threads are running.
    assert completion_time > (iterations * SLEEP_TIME)
    # If the completion time is longer than (iterations * SLEEP_TIME + 1) then
    # the code is probably not threaded properly.
    assert completion_time < ((iterations + 1) * SLEEP_TIME)
