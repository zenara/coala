# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json

from coalib.output.printers.ListLogPrinter import ListLogPrinter
from coalib.misc.StringConstants import StringConstants
from coalib.processes.Processing import execute_section
from coalib.settings.ConfigurationGathering import gather_configuration
from coalib.results.HiddenResult import HiddenResult
from coalib.misc.i18n import _
from coalib.output.JSONEncoder import JSONEncoder


def main():
    log_printer = ListLogPrinter()
    exitcode = 0
    results = {}
    try:
        yielded_results = False
        section_results = []

        (sections,
         local_bears,
         global_bears,
         targets) = gather_configuration(None, log_printer)

        for section_name in sections:
            section = sections[section_name]
            if not section.is_enabled(targets):
                continue

            section_result = execute_section(
                section=section,
                global_bear_list=global_bears[section_name],
                local_bear_list=local_bears[section_name],
                print_results=lambda *args: True,
                log_printer=log_printer,
                file_diff_dict={})
            yielded_results = yielded_results or section_result[0]

            results_for_section = []
            for i in [1, 2]:
                for key, value in section_result[i].items():
                    for result in value:
                        if isinstance(result, HiddenResult):
                            continue
                        results_for_section.append(result)
            results[section_name] = results_for_section

        if yielded_results:
            exitcode = 1
    except KeyboardInterrupt:  # Ctrl+C
        log_printer.warn(_("Program terminated by user."))
        exitcode = 130
    except EOFError:  # Ctrl+D
        log_printer.debug(_("Found EOF. Exiting gracefully."))
    except SystemExit as exception:
        exitcode = exception.code
    except Exception as exception:  # pylint: disable=broad-except
        log_printer.log_exception(StringConstants.CRASH_MESSAGE, exception)
        exitcode = 255

    retval = {"logs": log_printer.logs, "results": results}
    retval = json.dumps(retval,
                        cls=JSONEncoder,
                        sort_keys=True,
                        indent=2,
                        separators=(',', ': '))
    print(retval)

    return exitcode
