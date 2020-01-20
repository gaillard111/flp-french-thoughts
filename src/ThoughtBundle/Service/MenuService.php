<?php

namespace ThoughtBundle\Service;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Component\Translation\TranslatorInterface;

class MenuService
{
    /**
     * @var TranslatorInterface
     */
    private $translator;

    public function __construct(TranslatorInterface $translator)
    {
        $this->translator = $translator;
    }

    /**
     * @return array
     */
    public function makeMenu(User $user)
    {
        $menu = [];

        $menu[] = [
            'label' => $this->translator->trans('navbar.profile'),
            'route' => 'fos_user_profile_edit',
        ];

        $menu[] = [
            'label'      => $this->translator->trans('user.form.profile.profile_edit'),
            'route'      => 'thought_profile',
            'parameters' => [
                'userId' => $user->getId(),
            ],
        ];
        $menu[] = [
            'label' => $this->translator->trans('user.friendship.title'),
            'route' => 'friends',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.dialogs.title'),
            'route' => 'dialog_list',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.thought.create_page.title'),
            'route' => 'sonata_user_thought_create',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.thought.list_page.title'),
            'route' => 'sonata_user_thoughts',
        ];

        $menu[] = [
            'label' => $this->translator->trans('thought.menu.favorite_thoughts'),
            'route' => 'favorite-quotes',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.topic.list_page.title'),
            'route' => 'sonata_user_topics',
        ];

        $menu[] = [
            'label' => $this->translator->trans('user.chain.list_page.title'),
            'route' => 'sonata_user_chains',
        ];

        return $menu;
    }
}