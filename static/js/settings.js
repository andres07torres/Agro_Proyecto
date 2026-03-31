/**
 * AGRO VISOR - SETTINGS LOGIC
 * Manages user profile updates, password changes, and account security.
 */

async function guardarPerfil() {
    const btn = document.getElementById('btnSaveProfile');
    const originalText = btn.innerHTML;
    const lang = document.documentElement.lang || 'es';
    const isDark = document.documentElement.classList.contains('dark');

    btn.innerHTML = '<span class="material-symbols-outlined animate-spin text-sm mr-2">progress_activity</span> ' + (translations[lang]['btn_saving'] || "Guardando...");
    btn.disabled = true;

    try {
        const res = await fetch('/api/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({
                nombre: document.getElementById('inNombre').value,
                email: document.getElementById('inEmail').value
            })
        });
        const data = await res.json();
        if(!data.exito) throw new Error(data.error);
        
        Swal.fire({
            title: translations[lang]['swal_success_title'] || "¡Éxito!",
            text: translations[lang]['swal_profile_updated'] || "Perfil actualizado correctamente.",
            icon: "success",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
    } catch (e) {
        Swal.fire({
            title: translations[lang]['swal_error_title'] || "Error",
            text: e.message || "Error desconocido",
            icon: "error",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

async function guardarPassword() {
    const currentPass = document.getElementById('currentPass').value;
    const newPass = document.getElementById('newPass').value;
    const lang = document.documentElement.lang || 'es';
    const isDark = document.documentElement.classList.contains('dark');

    if (!currentPass || !newPass) {
        return Swal.fire({
            title: translations[lang]['swal_warning_title'] || "Aviso",
            text: translations[lang]['swal_fields_required'] || "Por favor complete todos los campos.",
            icon: "warning",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
    }
    if (newPass.length < 8) {
        return Swal.fire({
            title: translations[lang]['swal_security_title'] || "Seguridad",
            text: translations[lang]['swal_pass_min_length'] || "La contraseña debe tener al menos 8 caracteres.",
            icon: "info",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
    }
    
    const btn = document.getElementById('btnSavePass');
    btn.innerText = translations[lang]['btn_verifying'] || "Verificando...";
    btn.disabled = true;

    try {
        const res = await fetch('/api/profile/password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ current_password: currentPass, new_password: newPass })
        });
        const data = await res.json();
        if(!data.exito) throw new Error(data.error);
        
        Swal.fire({
            title: translations[lang]['swal_success_title'] || "¡Éxito!",
            text: translations[lang]['swal_pass_updated'] || "Su contraseña ha sido actualizada.",
            icon: "success",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
        
        if(window.addNotification) window.addNotification("Has cambiado tu contraseña.");
        
        document.getElementById('currentPass').value = '';
        document.getElementById('newPass').value = '';
        document.getElementById('passForm').classList.add('hidden');
    } catch (e) {
        Swal.fire({
            title: "Operación denegada",
            text: e.message || "Contraseña actual incorrecta",
            icon: "error",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
    } finally {
        btn.innerText = translations[lang]['btn_save'] || "Guardar";
        btn.disabled = false;
    }
}

async function toggle2FA() {
    const lang = document.documentElement.lang || 'es';
    const isDark = document.documentElement.classList.contains('dark');
    const btn = document.getElementById('btn2FA');
    
    if (btn) btn.classList.add('opacity-50', 'pointer-events-none');

    try {
        const res = await fetch('/api/profile/2fa', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        });
        const data = await res.json();
        if(!data.exito) throw new Error(data.error);

        window.location.reload();
    } catch (e) {
        Swal.fire({
            title: translations[lang]['swal_error_title'] || "Error",
            text: e.message || "Error al cambiar 2FA",
            icon: "error",
            background: isDark ? '#191c1d' : '#fff',
            color: isDark ? '#fff' : '#000'
        });
        if (btn) btn.classList.remove('opacity-50', 'pointer-events-none');
    }
}

async function eliminarCuenta() {
    const lang = document.documentElement.lang || 'es';
    const isDark = document.documentElement.classList.contains('dark');

    Swal.fire({
        title: translations[lang]['swal_danger_title'] || "¿Estás completamente seguro?",
        text: translations[lang]['swal_danger_text'] || "Se perderá todo el historial de datos cargados.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#ba1a1a",
        cancelButtonColor: "#3085d6",
        confirmButtonText: translations[lang]['btn_confirm_delete'] || "Sí, eliminar cuenta",
        cancelButtonText: translations[lang]['btn_cancel'] || "Cancelar",
        background: isDark ? '#191c1d' : '#fff',
        color: isDark ? '#fff' : '#000'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const res = await fetch('/api/profile/delete', {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    }
                });
                const data = await res.json();
                if(data.exito) {
                    window.location.href = '/inicio';
                } else throw new Error(data.error);
            } catch (e) {
                Swal.fire({
                    title: "Error",
                    text: e.message,
                    icon: "error",
                    background: isDark ? '#191c1d' : '#fff',
                    color: isDark ? '#fff' : '#000'
                });
            }
        }
    });
}
