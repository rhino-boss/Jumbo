#%%


import imageio


def generate_gif(fig_names, gif_name="test"):

    """
    genarate gif.

    Example
    ---
    pay_list = ["5", "10", "15", "20", "30", "40", "50", "100", "200", "350", "400", "750", "1000", "2000", "2500"]
    fig_names = []

    for pay in pay_list:
        fig_names.append(f"./Generate_Gif/倍率線型({pay}).jpg")

    >>> generate_gif(fig_names, "test")

    """

    gif_imgs = []
    for name in fig_names:
        gif_imgs.append(imageio.imread(name))

    imageio.mimsave(f"./Generate_Gif/{gif_name}.gif", gif_imgs, fps=3)


#%%
