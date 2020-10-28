<?php

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\UserBundle\Admin\Model\UserAdmin as BaseUserAdmin;


class UserAdmin extends BaseUserAdmin
{
    /**
     * @inheritdoc
     */
    public function getFormBuilder()
    {
        $this->formOptions['data_class'] = $this->getClass();

        $options                      = $this->formOptions;
        $options['validation_groups'] = (!$this->getSubject() || is_null($this->getSubject()->getId())) ? 'CustomRegistration' : 'CustomProfile';

        $formBuilder = $this->getFormContractor()->getFormBuilder($this->getUniqid(), $options);

        $this->defineFormBuilder($formBuilder);

        return $formBuilder;
    }

    protected function configureListFields(ListMapper $listMapper): void
    {
        $listMapper
            ->addIdentifier('email')
            ->add('enabled', null, [
                'editable' => true,
            ])
            ->add('createdAt')
            ->add('getRoleName', null, [
                'label' => 'Role'
            ])
        ;
    }

    protected function configureFormFields(FormMapper $formMapper): void
    {
        // define group zoning
        $formMapper
            ->tab('User')
            ->with('Profile', ['class' => 'col-md-6'])->end()
            ->with('General', ['class' => 'col-md-6'])->end()
            ->end()
        ;

        $now = new \DateTime();

        $formMapper
            ->tab('User')
            ->with('General')
            ->add('email')
            ->add('plainPassword', 'text', [
                'required' => (!$this->getSubject() || is_null($this->getSubject()->getId())),
            ])
            ->add('enabled')
            ->end()
            ->with('Profile')
            ->add('firstname', null, ['required' => false])
            ->add('lastname', null, ['required' => false])
            ->add('roles', 'choice', [
                'choices' => [
                    'ROLE_ADMIN'     => 'Admin',
                    'ROLE_MODERATOR' => 'Moderator',
                    'ROLE_USER'      => 'User',
                    'ROLE_TEACHER'   => 'Teacher',
                    'ROLE_STUDENT'   => 'Student',
                ],
                'expanded' => false,
                'multiple' => true,
                'required' => false,
            ])
            ->end()
            ->end()
        ;
    }

}
