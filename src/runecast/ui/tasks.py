# SPDX-License-Identifier: GPL-3.0-or-later
#
# RuneCast — traduction de jeux vidéo / video game translation
# Copyright (C) 2026 HARPUTOGLU David
# Créé par HARPUTOGLU David, aidé par l'IA / Created by HARPUTOGLU David, assisted by AI
# Contact : kasparof57@gmail.com
#
# FR : Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou
#      le modifier selon les termes de la Licence publique générale GNU (GNU GPL)
#      telle que publiée par la Free Software Foundation, soit la version 3 de
#      la licence, soit (à votre choix) toute version ultérieure.
#      Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS
#      AUCUNE GARANTIE, sans même la garantie implicite de QUALITÉ MARCHANDE ou
#      d'ADÉQUATION À UN USAGE PARTICULIER. Voir la GNU GPL pour plus de détails.
#      Vous devriez avoir reçu une copie de la GNU GPL avec ce programme
#      (fichier LICENSE). Sinon, voir <https://www.gnu.org/licenses/>.
#
# EN : This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program (LICENSE file). If not, see <https://www.gnu.org/licenses/>.

"""Travaux en arrière-plan / Background work.

FR : Les travaux longs (télécharger un modèle, traduire…) tournent dans un
     fil d'exécution séparé : la fenêtre reste fluide et ne se fige jamais.
     Le travail peut donner sa progression et être annulé.
EN : Long work (downloading a model, translating…) runs in a separate
     thread: the window stays smooth and never freezes. The work can report
     its progress and be cancelled.
"""

import logging
import threading
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)

# FR : Un travail reçoit deux fonctions : progression(fait, total) et
#      annulé() → bool. EN : A job receives two functions: progress(done,
#      total) and cancelled() → bool.
Work = Callable[[Callable[[int, int], None], Callable[[], bool]], Any]


class TaskThread(QThread):
    """Un travail en arrière-plan / A background job."""

    # FR : progression (fait, total). EN : progress (done, total).
    progress = Signal(int, int)
    # FR : terminé avec succès (résultat). EN : finished successfully (result).
    succeeded = Signal(object)
    # FR : échec (l'erreur). EN : failure (the error).
    failed = Signal(object)

    def __init__(self, work: Work, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.work = work
        self._cancel = threading.Event()

    def run(self) -> None:
        try:
            result = self.work(self.progress.emit, self._cancel.is_set)
        except Exception as error:  # noqa: BLE001 (toute erreur est remontée / any error is reported)
            logger.warning("Travail en échec / Job failed: %s", error)
            self.failed.emit(error)
        else:
            self.succeeded.emit(result)

    def cancel(self) -> None:
        """FR : demande l'arrêt (le travail s'arrête au prochain point de contrôle).

        EN : ask to stop (the job stops at its next checkpoint).
        """
        self._cancel.set()
