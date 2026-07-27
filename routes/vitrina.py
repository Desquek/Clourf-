import cloudinary
import cloudinary.uploader

@vitrina.route('/vitrina/novo', methods=['GET', 'POST'])
def vitrina_novo():
    if 'user_id' not in session:
        flash("Faça login para publicar.", "warning")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()
        preco = request.form.get('preco', '0').replace(',', '.')
        categoria = request.form.get('categoria', '')
        localizacao = request.form.get('localizacao', '').strip()

        if not titulo or not descricao or not preco or not categoria:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template('vitrina_novo.html')

        # Upload das fotos para o Cloudinary
        fotos = []
        for i in range(1, 5):
            foto = request.files.get(f'foto{i}')
            if foto and foto.filename:
                try:
                    upload_result = cloudinary.uploader.upload(
                        foto,
                        folder=f"clourf/produtos/{session['user_id']}",
                        transformation=[{'width': 600, 'height': 600, 'crop': 'limit'}]
                    )
                    fotos.append(upload_result['secure_url'])
                    print(f"✅ Foto {i} enviada para o Cloudinary!")
                except Exception as e:
                    print(f"❌ Erro ao fazer upload da foto {i}: {e}")

        # Guardar no banco (apenas os URLs)
        conn = get_db()
        cur = conn.cursor()
        is_postgres = hasattr(cur, 'mogrify')
        
        try:
            if is_postgres:
                cur.execute("""
                    INSERT INTO produtos (titulo, descricao, preco, categoria, localizacao, fotos, usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (titulo, descricao, float(preco), categoria, localizacao, fotos, session['user_id']))
            else:
                cur.execute("""
                    INSERT INTO produtos (titulo, descricao, preco, categoria, localizacao, fotos, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (titulo, descricao, float(preco), categoria, localizacao, json.dumps(fotos), session['user_id']))
            
            conn.commit()
            cur.close()
            conn.close()

            flash("Produto publicado com sucesso!", "success")
            return redirect(url_for('vitrina.vitrina_lista'))
        except Exception as e:
            print(f"❌ Erro ao publicar: {e}")
            flash("Erro ao publicar produto.", "danger")
            return render_template('vitrina_novo.html')

    return render_template('vitrina_novo.html')