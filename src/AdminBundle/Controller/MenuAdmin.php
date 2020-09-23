<?php

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use ThoughtBundle\Entity\MenuItem;

class MenuAdmin extends AbstractAdmin
{
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('text')
            ->add('parent.text')
            ->add('url')
            ->add('level')
            ->add('roleString', 'text', [
                'label' => 'Role',
            ])
            ->add('sort', 'text', [
                'label' => 'Priority',
            ])
        ;
    }

    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('text', 'text', [
                'label' => 'Title',
            ])
            ->add('parent', 'entity', [
                'class'        => MenuItem::class,
                'choice_label' => 'text',
                'required'     => false,
            ])
            ->add('url', 'text', [
                'required' => false,
            ])
            ->add('role', 'choice', [
                'choices' => [
                    'ROLE_ADMIN'                   => 'Admin',
                    'ROLE_USER'                    => 'User',
                    'IS_AUTHENTICATED_ANONYMOUSLY' => 'Unregistered',
                ],
            ])
            ->add('sort', 'integer', [
                'label'    => 'Priority',
                'required' => false,
            ])
        ;
    }

    public function toString($object)
    {
        return $object instanceof MenuItem
            ? $object->getText()
            : 'MenuItem';
    }
}